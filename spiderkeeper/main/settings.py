SERVERS = [
    ('测试', {'name': '测试', 'ip': ''}),
    ('PC同步监控', {'name': 'PC同步监控', 'ip': ''}),
    ('币须监控小程序', {'name': '币须监控小程序', 'ip': ''}),
    ('快讯采集1', {'name': '快讯采集1', 'ip': ''}),
    ('快讯采集2', {'name': '快讯采集2', 'ip': ''}),
]


REDIS_CONFIG = {
    'host': '192.168.5.216',
    'port': [6379, 6380],
    'db': [5, 6, 7],
    'passwd': 'erpteam_redis'
}


COUNTRYS = {'BiHu': u'币乎',
            'WeChat': u'微信',
            'Flash_Xcong': u'快讯小葱',
            'Flash_Jinse': u'快讯金色财经',
            'Flash_BiShiJie': u'快讯币世界',
            'Flash_Imeos': u'快讯imeos',
            'Flash_Chainnews': u'快讯chainnews',
            'Flash_Odaily': u'快讯odaily'}