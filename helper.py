import re


def pop_first_by_times(times: int, iter):
    pop_list = []
    for i in range(times):
        pop_list.append((iter.pop(0)))
    return pop_list


def get_basic_lists(iter):
    basic_list = []
    while True:
        if iter[0] == '23553d666ee6fdee341f45b602828368':
            pop_first_times = 3
        else:
            pop_first_times = 2
        pop_list = pop_first_by_times(times=pop_first_times, iter=iter)
        # print(pop_list)
        basic_list.append(pop_list)
        # 退出条件放最后，以便函数执行过一次再判断，可以去除搜索数据末尾不完整问题
        if len(iter) < 3:
            break
    return basic_list


def search_list_to_dict(basic_list):
    dic = {}
    if len(basic_list) == 3:
        dic['wechat_name'] = basic_list[1]
        dic['wechat_auth'] = True
        dic['wechat_summary'] = basic_list[2]
    else:
        dic['wechat_name'] = basic_list[0]
        dic['wechat_summary'] = basic_list[1]
    return dic


def parse_search_list(search_list):
    dic_list = []
    basic_lists = get_basic_lists(search_list)
    for basic_list in basic_lists:
        dic = search_list_to_dict(basic_list)
        dic_list.append(dic)
    return dic_list


if __name__ == '__main__':
    iter = [
        '23553d666ee6fdee341f45b602828368',
        '广州天环ParcCentral',
        '关注【天环Parc Central官方服务号】，主题活动、停车优惠、会员福利、品牌资讯马上Get！',

        'TOMS天环广场店',
        'TOMS 品牌 潮鞋 活动推广 新款推送',

        '23553d666ee6fdee341f45b602828368',
        '天环ParcCentral',
        '天环Parc Central，新鸿基华南纯商业首秀，创新塑造了“非凡时尚+”的多元购物理念，欲打造成为华南购物中心新地标。项目总面积约11万平方米，汇聚众多国际知名品牌、环球人气美食以及华南全新的LUXE影院，将为您带来尊崇享受！',

        '天环广场运动休闲集合店',
        '阿迪达斯广州天环广场运动休闲集合店',

        '广州天环广场adi自营店',
        '新品发布-活动信息-产品预订-产品咨询',

        '天环广场Lee牛仔',
        '地址：广州市天河区天环广场负二层B243 Lee牛仔 电话 ：020-22033097',

        'NB广州天环广场店',
        '位于广州天河区天环广场地下二层B212层铺。营业时间：10:00am~22:00pm 电话：37362671']

    dic = parse_search_list(iter)
    print(dic)
