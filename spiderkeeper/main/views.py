# -*- coding: utf-8 -*-
import pymongo
import redis
import json
import requests

from .conf import conf

from datetime import datetime
from collections import OrderedDict
from peewee import *

from flask import render_template, redirect, url_for, flash, make_response, jsonify, request

from flask import Blueprint
from . import basic_auth

from .settings import SERVERS, REDIS_CONFIG, COUNTRYS

main = Blueprint('main', __name__)


def select_config(port, db):
    return 'redis://:%(passwd)s@%(host)s:%(port)s/%(db)s' % \
                                {
                                    'passwd': REDIS_CONFIG['passwd'],
                                    'host': REDIS_CONFIG['host'],
                                    'port': REDIS_CONFIG['port'][port],
                                    'db': REDIS_CONFIG['db'][db]
                                }

r = redis.StrictRedis.from_url(select_config(0, 0))
r2 = redis.StrictRedis.from_url(select_config(-1, -1))
r3 = redis.StrictRedis.from_url(select_config(0, 1))

RDS_DICT = OrderedDict([
    (u'挖矿', {'name': r, 'ip': REDIS_CONFIG['host'], 'port': REDIS_CONFIG['port'][0], 'db': REDIS_CONFIG['db'][0]}),
    (u'销参', {'name': r2, 'ip': REDIS_CONFIG['host'], 'port': REDIS_CONFIG['port'][1], 'db': REDIS_CONFIG['db'][1]}),
    (u'Ebay', {'name': r3, 'ip': REDIS_CONFIG['host'], 'port': REDIS_CONFIG['port'][0], 'db': REDIS_CONFIG['db'][2]})
])


SPIDERS = {}
SERVERS = OrderedDict(SERVERS)


@main.route('/logs/<server>', methods=['GET', 'POST'])
def logs(server):
    url = 'http://' + SERVERS[server]['ip'] + ':6800/logs/'
    return render_template('scrapyd_log.html', url=url)


@main.route('/logs/<server>/<project>/<spider>/<sid>', methods=['GET', 'POST'])
def spider_log(server, project, spider, sid):
    url = 'http://' + SERVERS[server]['ip'] + ':6800/logs/' + project + '/' + spider + '/' + sid + '.log'
    return render_template('scrapyd_log.html', url=url)


@main.route('/listqueue/<server>', methods=['GET', 'POST'])
def listqueue(server):
    queue = OrderedDict()
    queue_format = OrderedDict()
    r_ = RDS_DICT[server]['name']
    keys_list = r_.keys()
    for keys in keys_list:
        try:
            ret = r_.zcard(keys.decode())
        except Exception as e:
            pass
        else:
            queue[keys.decode()] = ret

    queues = sorted(queue.items(), key=lambda x: x[0], reverse=True)
    dup = set()
    countrys = ['BiHu', 'WeChat', 'Flash_Xcong', 'Flash_Jinse', 'Flash_BiShiJie',
                'Flash_Imeos', 'Flash_Chainnews', 'Flash_Odaily']
    for q in queues:
        index = q[0].rfind('_')
        q_key = q[0][:index]
        if q_key not in dup:
            dup.add(q_key)
        queue_num = q[1]
        country = q[0].split(':')[0][index+1:]
        if not queue_format.get(q_key):
            queue_format[q_key] = {}
        queue_format[q_key][country] = queue_num
    return render_template('listqueue.html', countrys=countrys, queue=queue_format, server=server)


@main.route('/rediss', methods=['GET', 'POST'])
def rediss():
    redis_num = OrderedDict()
    index = 0
    for item in RDS_DICT:
        queue_set = set()
        index += 1
        rds_lst = RDS_DICT[item]['name'].keys()
        [queue_set.add(queue[:queue.rfind('_')]) for queue in rds_lst]
        if 'mysql' in queue_set:
            queue_set.remove('mysql')
        if 'mysql_lock' in rds_lst:
            rds_lst.remove('mysql_lock')
        redis_num[item] = RDS_DICT[item]
        redis_num[item]['num'] = len(rds_lst)
        redis_num[item]['index'] = index
        redis_num[item]['queue_num'] = len(queue_set)
    return render_template('redis_dashboard.html', redis_num=redis_num)


@main.route('/', methods=['GET', 'POST'])
@basic_auth.required
def index():
    running = OrderedDict()
    logs_num = OrderedDict()
    index = 0
    for server in SERVERS:
        try:
            info_json = requests.get('http://{0}:6800/daemonstatus.json'.format(SERVERS[server]['ip']), timeout=5).json()
            info_json['index'] = index
            running[server] = info_json
            logs_num[server] = {'ip': SERVERS[server]['ip'], 'status': 'active'}
            index += 1
        except Exception as e:
            running[server] = 'bad'
            logs_num[server] = {'ip': SERVERS[server]['ip'], 'status': 'bad', 'index': index}
    return render_template('job_dashboard.html', running=running, logs_num=logs_num)


@main.route('/listprojects/<server>')
def listprojects(server):
    f = requests.get('http://{0}:6800/listprojects.json'.format(SERVERS[server]['ip'])).json()
    projects = f['projects']

    projects_ebay, projects_wk, projects_xc = [[] for _ in range(3)]
    for pro in projects:
        if pro.startswith('ebay'):
            projects_ebay.append(pro)
        elif (pro.startswith('xc')) or (pro in ['keywordad', 'reviewfp']):
            projects_xc.append(pro)
        else:
            projects_wk.append(pro)

    running_ebay, running_wk, running_xc = [OrderedDict() for _ in range(3)]
    runnings = [(u'销参', running_xc), (u'ebay', running_ebay), (u'挖矿', running_wk)]
    for index, projects in enumerate([projects_xc, projects_ebay, projects_wk]):
        running = runnings[index][1]
        index = 0
        for project in projects:
            if not running.get(project, None):
                running[project] = {}
            jobs_info = requests.get('http://{0}:6800/listjobs.json?project={1}'.format(SERVERS[server]['ip'], project)).json()
            if not SPIDERS.get(server):
                SPIDERS[server] = {}
            if not SPIDERS[server].get(project):
                spider = len(requests.get('http://{0}:6800/listspiders.json?project={1}'.format(SERVERS[server]['ip'], project)).json()['spiders'])
                SPIDERS[server][project] = spider

            index += 1
            running[project]['index'] = index
            running[project]['spider'] = SPIDERS[server][project]
            for key, value in jobs_info.items():
                if isinstance(value, (str, unicode)):
                    running[project][key] = value
                else:
                    running[project][key] = len(value)

    return render_template('listprojects.html', server=server, runnings=OrderedDict(runnings), countrys=COUNTRYS)


@main.route('/projectstatus/<server>/<project>')
def projectstatus(server, project):
    projectstatus = requests.get('http://{0}:6800/listjobs.json?project={1}'.format(SERVERS[server]['ip'], project)).json()
    runnings, finisheds, pendings = [projectstatus[key] for key in list(projectstatus.keys())[1: 4]]
    for status_lst in [runnings, finisheds, pendings]:
        index = 0
        if status_lst:
            for ind, item_dic in enumerate(status_lst):
                item_dic_cp = item_dic
                if item_dic.get('end_time'):
                    fend_time = datetime.strptime(item_dic['end_time'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                    fstart_time = datetime.strptime(item_dic['start_time'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                    cost_time = str(fend_time - fstart_time)
                    item_dic['end_time'] = item_dic['end_time'].split('.')[0]
                    if cost_time == "0:00:01":
                        # print(item_dic)
                        status_lst.remove(item_dic_cp)
                    item_dic['cost_time'] = cost_time
                item_dic['index'] = index
                index += 1
                if item_dic.get('start_time'):
                    item_dic['start_time'] = item_dic['start_time'].split('.')[0]

    status_infos = {u'正在运行': runnings, u'已结束': finisheds, u'等待中': pendings}
    # return jsonify(status_infos)
    return render_template('projectstatus.html', status_infos=status_infos, server=server, project=project, countrys=COUNTRYS)


@main.route('/schedule/<server>/<project>/<spider>')
def schedule(server, project, spider):
    params = {'project': project, 'spider': spider}
    f = requests.post('http://{0}:6800/schedule.json'.format(SERVERS[server]['ip']), params=params)
    return f.content


@main.route('/create/<server>', methods=['GET', 'POST'])
def create(server):
    if request.method == "POST":
        project = request.form.get('project')
        spider = request.form.get('country')
        params = {'project': project, 'spider': spider}
        try:
            requests.post('http://{0}:6800/schedule.json'.format(SERVERS[server]['ip']), params=params)
            flash(u'启动 {0} 爬虫成功'.format(project))
        except:
            flash(u'启动 {0} 失败'.format(project))
    return redirect(url_for('main.listprojects', server=server))


@main.route('/cancel/<server>/<project>/<id>')
def cancel(server, project, id):
    params = {'project': project, 'job': id}
    try:
        res = requests.post('http://{0}:6800/cancel.json'.format(SERVERS[server]['ip']), params=params)
        flash(u'关闭 {0} 爬虫成功'.format(project))
    except:
        flash(u'关闭 {0} 爬虫失败'.format(project))
    return redirect(url_for('main.projectstatus', server=server, project=project))


@main.route('/force_cancel/<server>/<project>/<id>')
def force_cancel(server, project, id):
    params = {'project': project, 'job': id}
    try:
        for _ in range(2):
            requests.post('http://{0}:6800/cancel.json'.format(SERVERS[server]['ip']), params=params)
        flash(u'强制关闭 {0} 爬虫成功'.format(project))
    except:
        flash(u'强制关闭 {0} 爬虫失败'.format(project))
    return redirect(url_for('main.projectstatus', server=server, project=project))


@main.route('/close/<server>/<project>')
def close(server, project):
    f = requests.get('http://{0}:6800/listjobs.json?project={1}'.format(SERVERS[server]['ip'], project)).json()
    jobs = f['running']

    count = 0
    for job in jobs:
        params = {'project': project, 'job': job['id']}
        f = requests.post('http://{0}:6800/cancel.json'.format(SERVERS[server]['ip']), params=params).json()
        reply = f

        if reply['status'] == 'ok': count += 1

    flash(u'成功关闭 {0} 个爬虫'.format(count))

    return redirect(url_for('main.listjobs', server=server, project=project))


@main.route('/start/<server>/<project>')
def start(server, project):
    f = requests.get('http://{0}:6800/listjobs.json?project={1}'.format(SERVERS[server]['ip'], project)).json()
    jobs = f['running']
    f = requests.get('http://{0}:6800/listspiders.json?project={1}'.format(SERVERS[server]['ip'], project)).json()
    spiders = f['spiders']
    not_run_spiders = set(spiders) - set([job['spider'] for job in jobs])

    count = 0
    for spider in not_run_spiders:
        params = {'project': project, 'spider': spider}
        f = requests.post('http://{0}:6800/schedule.json'.format(SERVERS[server]['ip']), params=params).json()
        reply = f

        if reply['status'] == 'ok':
            count += 1

    flash(u'成功运行 {0} 个爬虫'.format(count))

    return redirect(url_for('main.listprojects', server=server))


@main.route('/businessreport/<id>')
def businessreport(id):
    class business_report(Model):
        id = IntegerField(primary_key=True)
        result = TextField()

        class Meta:
            conn = pymongo.MongoClient(
                'mongodb://{0}:{1}@{2}:{3}/'.format(conf.DB_UN, conf.DB_PW, conf.DB_HOST, conf.DB_PORT))

            db_table = conn[conf.DB_NAME]


    try:
        reply = business_report.get(business_report.id == int(id))
    except DoesNotExist:
        reply = None

    if reply is None:
        return u'id不存在'
    else:
        response = make_response(json.loads(reply.result)['report'])
        response.headers["Content-Disposition"] = "attachment; filename=%s.csv;" % json.loads(reply.result)['date']
        return response


@main.route('/test')
def test():
    return render_template('test.html')
