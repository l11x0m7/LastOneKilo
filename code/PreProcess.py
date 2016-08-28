#!/usr/bin/env python
# coding=utf-8

import sys
import pandas as pd
reload(sys)
sys.setdefaultencoding('utf-8')

class PreProcess:
	def __init__(self, filepath=None, names=None):
		if not filepath:
			return
		self.data_list = pd.read_csv(filepath, header=0, index_col=0, names=names)
		# print courier_list
	def getPanda(self):
		return self.data_list
	def drawMap(self, pointname, *pplist):
		from matplotlib import pyplot as plt
		color = ['r', 'g', 'b']
		plt.figure(1)
		plt.subplot(111)
		plt.xlabel('Lng')
		plt.ylabel('Lat')
		for i, each_pp in enumerate(pplist):
			try:
				if pointname == None:
					plt.scatter(each_pp.Lng, each_pp.Lat, color=color[i%3])
				else:
					plt.scatter(each_pp.Lng, each_pp.Lat, color=color[i%3], label=pointname[i%3])
			except AttributeError:
				print 'The arg %d is not appropriate.' % (i+1)
				return
		if pointname:
			plt.legend(loc = 'upper left' , fontsize = 'x-small')
		plt.show()

if __name__ == '__main__':
	# 网点
	pp_wang = PreProcess('../data/new_1.csv', names=['Lng','Lat'])
	# 配送点
	pp_pei = PreProcess('../data/new_2.csv', names=['Lng','Lat'])
	# 商户点
	pp_shop = PreProcess('../data/new_3.csv', names=['Lng', 'Lat'])
	# 电商订单
	pp_dian_order = PreProcess('../data/new_4.csv', names=['SpotID', 'SiteID', 'Num'])
	# O2O订单
	pp_o2o_order = PreProcess('../data/new_5.csv', names=['SpotID', 'ShopID', 'PickupTime', 'DeliverTime', 'Num'])
	# 快递员ID
	pp_courier = PreProcess('../data/new_6.csv', names=[])

	wangdian = pp_wang.getPanda()
	peisong = pp_pei.getPanda()
	shop = pp_shop.getPanda()
	dian_order = pp_dian_order.getPanda()
	o2o_order = pp_o2o_order.getPanda()
	courier = pp_courier.getPanda()

	pp = PreProcess()
	pp.drawMap(['peisong', 'wangdian', 'shop'], peisong, wangdian, shop)


