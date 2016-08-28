#!/usr/bin/env python
# coding=utf-8

import sys
import pandas as pd
import math
import numpy as np
import MySQLdb
import datetime
from pyevolve import G1DList
from pyevolve.GSimpleGA import GSimpleGA
from ga import Generation
reload(sys)
sys.setdefaultencoding('utf-8')
# 地球半径
_R = 6378.137
# 车速:公里/分钟
VELOCITY = 0.25

# 参数设置
# 最大承载包裹数
max_carriage = 140
# 快递员工作时间
start_work = 8
end_work = 20
max_work_minute = (end_work-start_work) * 60

class OneKilo():
	def __init__(self):
		self.filelist = ['../data/new_' + str(i) + '.csv' for i in range(1, 7)]
		# 网点
		self.wangdian = pd.read_csv(self.filelist[0], names=['Lng', 'Lat'], index_col=0)
		# 配送点
		self.peisong = pd.read_csv(self.filelist[1], names=['Lng', 'Lat'], index_col=0)
		# 商户
		self.shop = pd.read_csv(self.filelist[2], names=['Lng', 'Lat'], index_col=0)
		# 电商订单
		self.dian_order = pd.read_csv(self.filelist[3], names=['SpotID', 'SiteID', 'Num'], index_col=0)
		# O2O订单
		self.o2o_order = pd.read_csv(self.filelist[4], names=['SpotID', 'ShopID', 'PickupTime', 'DeliverTime', 'Num'], index_col=0)
		# 送货员ID
		self.courier = pd.read_csv(self.filelist[5], names=[], index_col=0)
		# 送货员使用情况
		self.courier_use = 0
		self.conn = MySQLdb.connect(host='localhost', user='root', db='onkilo', charset='utf8')
		self.cur = self.conn.cursor()
		self.gnome = G1DList.G1DList(10)
		self.GAGenerator = GSimpleGA

	def distance(self, psd_lng, wd_lng, psd_lat, wd_lat):
		delta_lng = psd_lng - wd_lng
		delta_lat = psd_lat - wd_lat
		return \
		round(2 * _R * math.asin(math.sqrt(math.sin(math.pi*delta_lat/180)**2\
			+ math.cos(math.pi*wd_lat/180)*math.cos(math.pi*psd_lat/180)\
			*math.sin(math.pi*delta_lng/180)**2))/VELOCITY)

	def stayTime(self, pacnum):
		return int(round(3 * math.sqrt(pacnum) + 5))

	def transToMinute(self, t):
		t = t.split(':')
		return (int(t[0]) - 8) * 60 + int(t[1])

	def dianShangFitness(self, chromosome):
		# print chromosome
		# 该配送区分配的配送员人数
		courier_num = chromosome[0]
		# 路径顺序
		route_seq = chromosome[1:]
		# 获取网点信息
		spotid = self.intid_spotid[0][0]
		wdlng = self.wangdian.ix[spotid].Lng
		wdlat = self.wangdian.ix[spotid].Lat
		# 记录每个配送员的活动时间
		time_seq = [0]*courier_num
		# 记录每个配送员的配送包裹数
		carry_seq = [0]*courier_num
		# 记录courier_info里每个配送员的起始拿包的下标(一开始是0)
		start_index = [0]*courier_num
		# 记录当前的访问顺序号
		cur_courier = 0
		# 记录上次访问的spot_intid
		last_spot = [0]*courier_num
		# 记录每个配送员的详细信息
		courier_info = dict()
		# 按配送员的当前时间进行排序,时间小(说明早回来)的排前面
		indeces = range(0, courier_num)
		# 当前实际访问的配送员id
		cur_real_courier = indeces[cur_courier]
		# 遍历所有路径序列,分配配送员
		curi = 0
		while curi < len(route_seq):
			spot_intid = route_seq[curi]
			# 获得当前配送点的信息
			spotid, pacnum, orderid = self.intid_spotid[spot_intid]
			spotlng = self.peisong.ix[spotid].Lng
			spotlat = self.peisong.ix[spotid].Lat
			# 如果该配送员仍可以携带该配送点的包裹,则佩戴,否则移动到下一个
			if carry_seq[cur_real_courier]+pacnum <= max_carriage:
				# 如果该配送员上一位置不在网点,则需要回来
				if last_spot[cur_real_courier] != 0:
					last_spotid, last_pacnum, last_orderid = self.intid_spotid[last_spot[cur_real_courier]]
					last_spotlng = self.peisong.ix[last_spotid].Lng
					last_spotlat = self.peisong.ix[last_spotid].Lat
					back_dis = self.distance(wdlng, last_spotlng, wdlat, last_spotlat)
					last_spot[cur_real_courier] = 0
					time_seq[cur_real_courier] += back_dis
				# 将当前配送点的订单给当前的配送员
				carry_seq[cur_real_courier] += pacnum
				courier_info.setdefault(cur_real_courier, list())
				courier_info[cur_real_courier].append\
					((spot_intid, spotid, time_seq[cur_real_courier], time_seq[cur_real_courier], pacnum, orderid))
				# 移动到下一个配送点
				curi += 1
			else:
				# 移动到下一个配送员
				cur_courier += 1
			# 如果新完成一轮(所有配送员都接过单),则需要更新该轮信息,即运送货物,之后重新继续分配剩余的任务
			if cur_courier >= courier_num or curi == len(route_seq):
				back_home_dis = np.zeros(courier_num)
				for courierid in courier_info:
					if last_spot[courierid] != 0:
						continue
					new_tasks = courier_info[courierid][start_index[courierid]:]
					start_index[courierid] += len(new_tasks)
					for task in new_tasks:
						if last_spot[courierid] == 0:
							last_spotid, _, _ = self.intid_spotid[last_spot[courierid]]
							last_spotlng = self.wangdian.ix[last_spotid].Lng
							last_spotlat = self.wangdian.ix[last_spotid].Lat
						else:
							last_spotid, _, _ = self.intid_spotid[last_spot[courierid]]
							last_spotlng = self.peisong.ix[last_spotid].Lng
							last_spotlat = self.peisong.ix[last_spotid].Lat
						spotlng = self.peisong.ix[task[1]].Lng
						spotlat = self.peisong.ix[task[1]].Lat
						last_spot[courierid] = task[0]
						mov_time = self.distance(spotlng, last_spotlng, spotlat, last_spotlat)
						process_time = self.stayTime(task[4])
						courier_info[courierid].append((task[0], task[1], time_seq[courierid]+mov_time, time_seq[courierid]+mov_time+process_time, -task[4], task[5]))
						time_seq[courierid] += (mov_time + process_time)
						carry_seq[courierid] -= task[4]
					back_home_dis[courierid] = self.distance(wdlng, spotlng, wdlat, spotlat)

				tmp_time_seq = (time_seq+back_home_dis).tolist()
				indeces = np.argsort(tmp_time_seq)
				cur_courier = 0
			cur_real_courier = indeces[cur_courier]
		F1 = sum(time_seq)
		F2 = len(np.nonzero(time_seq)[0])
		# print F1, F2
		while F1>0.1:
			F1 /= 10.0
		while F2>0.1:
			F2 /= 10.0
		return 1.0/(F1+F2), courier_info


	def dianShang(self):
		site_pacnum = dict()
		all_sites = set(self.dian_order.SiteID)
		# print all_sites
		for siteid in all_sites:
			site2pac = self.dian_order.ix[self.dian_order.SiteID==siteid, 'Num'].values
			site_pacnum[siteid] = (len(site2pac), sum(site2pac))

		self.site_pacnum = pd.DataFrame(data=site_pacnum.values(), index=site_pacnum.keys(), columns=['Spotnum', 'Num'])
		print len(all_sites)
		count = 0
		for siteid in self.site_pacnum.index:
			courier_num = int(self.site_pacnum.ix[siteid, 'Num']/max_carriage)+1
			max_courier_num = self.site_pacnum.ix[siteid, 'Spotnum']
			spot_num = max_courier_num
			spot_list = self.dian_order.ix[self.dian_order.SiteID==siteid, 'SpotID']
			pacnum_list = self.dian_order.ix[self.dian_order.SiteID==siteid, 'Num']
			orderid_list = self.dian_order.ix[self.dian_order.SiteID==siteid].index
			zipper = zip(spot_list, pacnum_list, orderid_list)
			self.intid_spotid = dict(zip(range(1, spot_num+1), zipper))
			self.intid_spotid.update({0:(siteid, 0, '')})
			g = Generation(self.dianShangFitness, groupnum=4, generation=5, var_num=1+spot_num, crossrate=0.8, variationrate=0.8, var_minrange=[courier_num], var_maxrange=[max_courier_num], decodemap=self.intid_spotid)
			fitness, route, courier_spot = g.geneEvolve()
			print fitness, route
			courier_list, courier_spot = zip(*sorted(courier_spot.iteritems(), key=lambda kk:kk[0]))
			for i, courierid in enumerate(courier_list):
				cur_courierid = 'D%04d' % (self.courier_use+courierid+1)
				for item in courier_spot[i]:
					if item[4] < 0:
						addr = str(siteid)
					else:
						addr = str(item[1])
					arr_time, leave_time, amount, order_id = str(item[2]), str(item[3]), str(item[4]), str(item[5])
					print '\t'.join([cur_courierid, addr, arr_time, leave_time, amount, order_id])
			self.courier_use += len(courier_list)
			count += 1
			if count == 1:
				break




		# self.gnome.setParams(rangemin=0, rangemax=15)
		# self.gnome.evaluator.set(self.dianShangFitness)
		# self.ga = self.GAGenerator(self.gnome)
		# self.ga.evolve(freq_stats=10)
		# print self.ga.bestIndividual()



	def writeDB(self, sql):
		ct_sql = r"create table if not exists dianshang(name varchar(128) primary key, created int(10));"

		self.cur.execute(sql)
		self.conn.commit()

	def ConciseInfo(self):
		wangdian = self.wangdian
		peisong = self.peisong
		shop = self.shop
		dian_order = self.dian_order
		o2o_order = self.o2o_order
		courier = self.courier
		print len(dian_order)
		print len(o2o_order)

		wd2psd_dist = dict()
		wd2psd_pacnum = dict()
		place_num = 0
		for wd_id in wangdian.index:
			wd_lng = float(wangdian[wangdian.index==wd_id].Lng.values[0])
			wd_lat = float(wangdian[wangdian.index==wd_id].Lat.values[0])
			spotsid = dian_order.ix[dian_order.SiteID==wd_id, 'SpotID'].values
			for spotid in spotsid:
				psd_lng = peisong.ix[peisong.index==spotid, 'Lng'].values[0]
				psd_lat = peisong.ix[peisong.index==spotid, 'Lat'].values[0]
				pacnum = dian_order.ix[dian_order.SpotID==spotid, 'Num'].values[0]

				S = self.distance(psd_lng, wd_lng, psd_lat, wd_lat)
				wd2psd_dist.setdefault(wd_id, dict())
				if not wd2psd_dist[wd_id].has_key(spotid):
					place_num += 1
				wd2psd_dist[wd_id][spotid] = S
				wd2psd_pacnum.setdefault(wd_id, dict())
				wd2psd_pacnum[wd_id][spotid] = pacnum

		print place_num
		max_sitenum = 0
		max_pacnum = 0
		for spotid in wd2psd_pacnum:
			max_sitenum = max(max_sitenum, len(wd2psd_pacnum[spotid]))
			max_pacnum = max(max_pacnum, *wd2psd_pacnum[spotid].values())
		print max_sitenum, max_pacnum

		ds2psd_dist = dict()
		ps2psd_pacinfo = dict()
		place_num = 0
		for shop_id in shop.index:
			shop_lng = float(shop[shop.index==shop_id].Lng.values[0])
			shop_lat = float(shop[shop.index==shop_id].Lat.values[0])
			spotsid = o2o_order.ix[o2o_order.ShopID==shop_id, 'SpotID'].values
			for spotid in spotsid:
				psd_lng = peisong.ix[peisong.index==spotid, 'Lng'].values[0]
				psd_lat = peisong.ix[peisong.index==spotid, 'Lat'].values[0]
				total_pacnum = o2o_order.ix[o2o_order.SpotID==spotid, 'Num'].values
				total_pt = o2o_order.ix[o2o_order.SpotID==spotid, 'PickupTime'].values
				total_dt = o2o_order.ix[o2o_order.SpotID==spotid, 'DeliverTime'].values
				total_num = len(total_pt)
				for i in range(total_num):
					pt = self.transToMinute(total_pt[i])
					dt = self.transToMinute(total_dt[i])
					pacnum = total_pacnum[i]
					ps2psd_pacinfo.setdefault(shop_id, dict())
					ps2psd_pacinfo[shop_id][spotid] = (pt, dt, pacnum)

				S = self.distance(psd_lng, shop_lng, psd_lat, shop_lat)
				ds2psd_dist.setdefault(shop_id, dict())
				if not ds2psd_dist[shop_id].has_key(spotid):
					place_num += 1
				ds2psd_dist[shop_id][spotid] = S

		max_shopnum = 0
		for spotid in ps2psd_pacinfo:
			max_shopnum =max(max_shopnum, len(ps2psd_pacinfo[spotid]))
		print max_shopnum

		print place_num





if __name__ == '__main__':
	ok = OneKilo()
	ok.dianShang()
	# ok.ConciseInfo()