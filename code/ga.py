#coding:utf8
import os
import sys
import math
import random
from random import shuffle
import re
import datetime
import logging
import json
import copy
import numpy as np
reload(sys)
sys.setdefaultencoding('utf8')
logging.basicConfig(level=logging.INFO,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                stream=sys.stdout)


class Generation:
    def __init__(self, aim, groupnum=10, generation=50, var_num=2, crossrate=0.8, variationrate=0.8, var_minrange=[0, 0], var_maxrange=[7,7], decodemap=dict()):
        # 适应度函数
        self.aim = aim
        # 种群数量
        self.groupnum = groupnum
        # 变量数
        self.var_num = var_num
        # 繁殖代数
        self.generation = generation
        # 当前代数
        self.curiter = 1
        # 交叉概率
        self.crossrate = crossrate
        # 变异概率
        self.variationrate = variationrate
        # log日志
        self.logger = logging.log
        # 变量下限取值范围，[a, b]
        self.var_minrange = var_minrange
        # 变量上限取值范围，[c, d]
        self.var_maxrange = var_maxrange
        # 数字映射为相应网点/配送点的ID
        # 种群结果
        self.population = list()

        cur_init = range(1, var_num)
        for i in range(groupnum):
            shuffle(cur_init)
            p_tmp = [random.randint(self.var_minrange[0], self.var_maxrange[0])] + copy.copy(cur_init)
            self.population.append(p_tmp)
        # print self.population
        # 记录最好的结果
        self.best = list()

    # 基因解码
    # pop:list()
    def geneDecode(self, pop):
        cut_p = -1
        decode_pop = list()
        for i in range(self.var_num):
            base = 1
            decimal = 0
            for bit in pop[cut_p:cut_p-self.encodebit:-1]:
                decimal += bit * base
                base *= 2
            cut_p = cut_p - self.encodebit
            decode_pop.append(float(self.var_maxrange[i]-self.var_minrange[i])*decimal/(2**self.encodebit-1) + self.var_minrange[i])
        return decode_pop

    # 计算适应度
    def calcSufficiency(self):
        survival_list = list()
        courier_spots_list = list()
        for pop in self.population:
            survival_rate, courier_spots = self.aim(pop)
            survival_list.append(survival_rate)
            courier_spots_list.append(courier_spots)
        total = float(sum(survival_list))
        rate_survival_list = [rate/total for rate in survival_list]
        index = np.argsort(rate_survival_list)[-1]
        # print self.population, decode_list
        self.best.append((survival_list[index], copy.copy(self.population[index]), courier_spots_list[index]))
        # print self.best[-1]
        # self.logger(logging.INFO, '{0} The survival rate of each population is: '.format(self.curiter) + '\n' + json.dumps(rate_survival_list))
        self.curiter += 1
        return rate_survival_list

    # 基因选择
    def choosePopulation(self):
        survival_list = self.calcSufficiency()
        for i in xrange(1, len(survival_list)):
            survival_list[i] += survival_list[i-1]
        
        new_population = list()
        for curgroup in range(self.groupnum):
            random_rate = random.random()
            for i, prop in enumerate(survival_list):
                if random_rate <= prop:
                    new_population.append(copy.copy(self.population[i]))
                    break
        self.population = new_population
        return new_population

    # 交叉
    def crossCalc(self):
        self.choosePopulation()
        np.random.shuffle(self.population)
        # self.logger(logging.INFO, self.population)
        for i in range(0, self.groupnum, 2):
            prop = random.random()
            rand_cross_point = random.randint(2, self.var_num-1)
            # print prop, rand_cross_point
            if prop <= self.crossrate:
                # print i, self.population[i], self.population[i+1]
                i_set = set(self.population[i+1][1:rand_cross_point])
                total_set = set(range(1, self.var_num))
                ip1_set = set(self.population[i][1:rand_cross_point])
                self.population[i][1:rand_cross_point], self.population[i+1][1:rand_cross_point] = \
                    copy.copy(self.population[i+1][1:rand_cross_point]), copy.copy(self.population[i][1:rand_cross_point])
                for leftpart in range(rand_cross_point, self.var_num):
                    if self.population[i][leftpart] in i_set:
                        cur_set = total_set - i_set
                        self.population[i][leftpart] = list(cur_set)[random.randint(0, len(cur_set)-1)]
                    i_set.add(self.population[i][leftpart])

                    if self.population[i+1][leftpart] in ip1_set:
                        cur_set = total_set - ip1_set
                        self.population[i+1][leftpart] = list(cur_set)[random.randint(0, len(cur_set)-1)]
                    ip1_set.add(self.population[i+1][leftpart])
                # print self.population[i], self.population[i+1]
        # self.logger(logging.INFO, self.population)
        return self.population

    # 基因突变
    def geneRevolution(self):
        self.crossCalc()
        # print self.population
        for i in range(self.groupnum):
            rand_variation_num = random.randint(1, self.var_num)
            # rand_variation_num = 1
            for j in range(rand_variation_num):
                prop = random.random()
                if prop <= self.variationrate:
                    rand_variation_point1 = random.randint(1, self.var_num-1)
                    while True:
                        rand_variation_point2 = random.randint(1, self.var_num-1)
                        if(rand_variation_point2 != rand_variation_point1):
                            break
                    self.population[i][rand_variation_point1], self.population[i][rand_variation_point2] = \
                        self.population[i][rand_variation_point2], self.population[i][rand_variation_point1]
        # print self.population
        return self.population

    # 基因进化
    def geneEvolve(self):
        for i in range(self.generation):
            self.geneRevolution()

        self.best.sort(key=lambda kk:kk[0])
        # print self.best[-1]
        return self.best[-1]



if __name__ == '__main__':
    aim = lambda x:sum(k**2 for k in x)
    g = Generation(aim, groupnum=60, generation=100, var_num=10, var_minrange=[1],var_maxrange=[4], decodemap=dict())
    g.geneEvolve()


