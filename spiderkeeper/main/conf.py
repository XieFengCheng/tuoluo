# -*- coding: utf8 -*-
import os


class Config(object):
    # flask是否开启debug模式
    DEBUG = True
    # 数据库名
    DB_NAME = ''
    # 数据库IP地址
    DB_HOST = ''
    # 数据库端口
    DB_PORT = 27017
    # 数据库账号
    DB_UN = ''
    # 数据库密码
    DB_PW = ''

    # Redis IP地址
    R_HOST = ''
    # Redis 端口
    R_PORT = 6379
    # Redis 密码
    R_AUTH = ''



class DevelopConfig(Config):
    """
    开发环境
    """

    # flask端口
    PORT = 8090
    DEBUG = True


class TestingConfig(Config):
    """
    测试环境
    """
    # 数据库IP地址
    DB_HOST = '127.0.0.1'

    # Redis IP地址
    R_HOST = '127.0.0.1'
    # Redis 端口
    R_PORT = 6377
    # Redis 密码
    R_AUTH = ''


class ProductionConfig(Config):
    """
    生成环境
    """
    # 数据库名
    DB_NAME = ''

    # 数据库IP地址
    DB_HOST = ''
    # 数据库端口
    DB_PORT = 29876
    # 数据库账号
    DB_UN = ''
    # 数据库密码
    DB_PW = ''

    # Redis IP地址
    R_HOST = ''
    # Redis 端口
    R_PORT = 6377
    # Redis 密码
    R_AUTH = ''


# 系统配置
conf = None
# 系统环境变量
conf_ver = None
# 系统环境名称
conf_env = None

# 自动判断环境生产config
if os.path.exists('production.conf'):
    conf = ProductionConfig()
    conf_ver = 'conf.ProductionConfig'
    conf_env = u'生产环境'
elif os.path.exists('test.conf'):
    conf = TestingConfig()
    conf_ver = 'conf.TestingConfig'
    conf_env = u'测试环境'
else:
    conf = DevelopConfig()
    conf_ver = 'conf.DevelopConfig'
    conf_env = u'开发环境'


