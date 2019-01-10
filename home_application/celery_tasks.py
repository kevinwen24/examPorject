# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making 蓝鲸智云(BlueKing) available.
Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations under the License.

celery 任务示例

本地启动celery命令: python  manage.py  celery  worker  --settings=settings
周期性任务还需要启动celery调度命令：python  manage.py  celerybeat --settings=settings
"""
import datetime

from celery import task
from celery.schedules import crontab
from celery.task import periodic_task

from common.log import logger
import base64
import time
from blueking.component.shortcuts import get_client_by_user
from common.mymako import render_json
from home_application.models import operationLog


@task()
def async_task(bk_biz_id, biz_name, account, ip_string, job_id, ip_list, script_param):
    """
    定义一个 celery 异步任务
    """

    client = get_client_by_user(account)
    client.set_bk_api_ver('v2')

    res = client.job.execute_job({
        'bk_biz_id': bk_biz_id,
        'ip_list': ip_list,
        'bk_job_id': job_id,
        'global_vars': {
            "ip_list": ip_list
        }
    })
    task_id = res.get("data").get("job_instance_id")

    if not res.get("result"):
        return render_json(res)

    while not client.job.get_job_instance_status({
        'bk_biz_id': bk_biz_id,
        'job_instance_id': task_id,
    }).get('data').get('is_finished'):
        print 'waiting job finished...'
        time.sleep(1.2)

    res = client.job.get_job_instance_log({
        'bk_biz_id': bk_biz_id,
        'job_instance_id': task_id
    })

    log_content = res['data'][0]['step_results'][0]['ip_logs']

    success_ip = []
    failure_ip = []
    for item in log_content:
        print item.get("log_content")

        if item.get("exit_code") == 0:
            success_ip.append(item.get("log_content"))
        else:
            failure_ip.append(item.get("log_content"))

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result_message = success_ip
    operationLog.objects.create(
        biz_name=biz_name,
        operator=account,
        operate_date=current_time,
        job_id=job_id,
        host_ip=ip_string,
        status="successed",
        operate_log=result_message,
    )


def execute_task():
    """
    执行 celery 异步任务

    调用celery任务方法:
        task.delay(arg1, arg2, kwarg1='x', kwarg2='y')
        task.apply_async(args=[arg1, arg2], kwargs={'kwarg1': 'x', 'kwarg2': 'y'})
        delay(): 简便方法，类似调用普通函数
        apply_async(): 设置celery的额外执行选项时必须使用该方法，如定时（eta）等
                      详见 ：http://celery.readthedocs.org/en/latest/userguide/calling.html
    """
    now = datetime.datetime.now()
    logger.error(u"celery 定时任务启动，将在60s后执行，当前时间：{}".format(now))
    # 调用定时任务
    async_task.apply_async(args=[now.hour, now.minute], eta=now + datetime.timedelta(seconds=60))


def execute_task(bk_biz_id, biz_name, account, ip_string, job_id, ip_list, script_param):
    """
    执行 celery 异步任务

    调用celery任务方法:
        task.delay(arg1, arg2, kwarg1='x', kwarg2='y')
        task.apply_async(args=[arg1, arg2], kwargs={'kwarg1': 'x', 'kwarg2': 'y'})
        delay(): 简便方法，类似调用普通函数
        apply_async(): 设置celery的额外执行选项时必须使用该方法，如定时（eta）等
                      详见 ：http://celery.readthedocs.org/en/latest/userguide/calling.html
    """
    async_task.delay(bk_biz_id, biz_name, account, ip_string, job_id, ip_list, script_param)


@periodic_task(run_every=crontab(minute='*/5', hour='*', day_of_week="*"))
def get_time():
    """
    celery 周期任务示例

    run_every=crontab(minute='*/5', hour='*', day_of_week="*")：每 5 分钟执行一次任务
    periodic_task：程序运行时自动触发周期任务
    """
    # execute_task()
    # now = datetime.datetime.now()
    # logger.error(u"celery 周期任务调用成功，当前时间：{}".format(now))
    pass
