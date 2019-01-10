# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making 蓝鲸智云(BlueKing) available.
Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations under the License.
"""

from blueking.component.shortcuts import get_client_by_request
import logging as logger
from biz_utils import get_app_by_user
from common.mymako import render_mako_context, render_json, render_mako_tostring
import datetime
from home_application.celery_tasks import execute_task
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from home_application import models

def test(request):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_json({
        'result': True,
        'message': "success",
        'data': {
            'user': request.user.username,
            "time": current_time
        }
    })

def home(request):
    """
    首页
    """
    client = get_client_by_request(request)
    client.set_bk_api_ver('v2')

    res = client.cc.search_business()
    bizs = []
    if res.get("result", False):
        bizs = res.get("data").get("info")
    else:
        logger.error(u"请求业务失败: %s" % res.get("message"))

    return render_mako_context(request, '/home_application/home.html', {"bizs": bizs})


def get_set_by_biz(request):
    biz_id = request.POST.get("bizId")
    client = get_client_by_request(request)
    client.set_bk_api_ver('v2')

    if not biz_id:
        return render_json({
            'result': False,
            'data': "业务id不合法"
        })

    set_res = client.cc.search_set({
        'bk_biz_id': biz_id,
    })

    set_list=[]
    if set_res.get('result'):
        set_list = set_res.get('data').get('info')

    return render_json({
            'result': True,
            'data': set_list
        })


def get_hosts_by_biz_set(request):
    client = get_client_by_request(request)
    client.set_bk_api_ver('v2')

    biz_id = request.POST.get("bizId")
    set_id = request.POST.get("setId")
    kwargs = {'bk_biz_id': biz_id, 'set_id': set_id}
    res = client.cc.search_host(kwargs)
    contents = []
    if res.get("result", False):
        contents = res.get("data").get("info")
    else:
        logger.error(u"请求业务失败: %s" % res.get("message"))

    hosts=[]
    for content in contents:

        host = content.get("host")
        item = {
            "bk_host_innerip": host.get("bk_host_innerip"),
            "bk_os_name": host.get("bk_os_name"),
            "bk_host_name": host.get("bk_host_name"),
            "bk_cloud_name": host.get("bk_cloud_id")[0].get("bk_inst_name"),
            "bk_inst_id": host.get("bk_cloud_id")[0].get("bk_inst_id"),
        }
        hosts.append(item)

    contentString = render_mako_tostring('/home_application/tbody_host.html', {
        'bk_host_list': hosts
    })

    return render_json({
            'result': True,
            'data': contentString
        })


def execute_script(request):
    bk_biz_id = request.POST.get("bizId")
    bk_cloud_id = request.POST.get("bkCloudId")
    choise_hosts = request.POST.get("choiseHosts")
    biz_name = request.POST.get("bizName")

    host_string = ''
    ipList = []
    for hostItem in choise_hosts.split(","):
        ipItem = {
            "bk_cloud_id": bk_cloud_id,
            "ip": hostItem
        }
        ipList.append(ipItem)
        host_string += hostItem

    script_param = ""
    account=request.user.username
    job_id=1019
    execute_task(bk_biz_id, biz_name, account, host_string, job_id, ipList, script_param)
    return render_json({
        'result': True,
        'data': '任务提交成功'})


@csrf_protect
def execute_history(request):
    client = get_client_by_request(request)
    client.set_bk_api_ver('v2')

    res = client.cc.search_business()
    bizs = []
    if res.get("result", False):
        bizs = res.get("data").get("info")
    else:
        logger.error(u"请求业务失败: %s" % res.get("message"))

    bizId = request.POST.get("bizId")
    startTime = request.POST.get("startTime")
    endTime = request.POST.get("endTime")

    if not bizId:
        operationLogs = models.operationLog.objects.order_by("-operate_date")
    else:
        operationLogs = models.operationLog.objects.filter(biz_name=bizId, operate_date__gte=startTime,
                                                           operate_date__lte=endTime).order_by("-operate_date")
    return render_mako_context(request, '/home_application/history.html', {"operationLogs": operationLogs, "bizs": bizs})



def dev_guide(request):
    """
    开发指引
    """
    return render_mako_context(request, '/home_application/dev_guide.html')


def contactus(request):
    """
    联系我们
    """
    return render_mako_context(request, '/home_application/contact.html')
