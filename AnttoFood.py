# Python3.9, UTF-8
import random
import pygame
import sys
from pygame.locals import *

# 一些常数的定义
WINDOW_W, WINDOW_H = 1200, 800  # 窗体尺寸
ANT_SIZE = 5
assert WINDOW_W % ANT_SIZE == 0
assert WINDOW_H % ANT_SIZE == 0
WORLD_W = int(WINDOW_W/ANT_SIZE)
WORLD_H = int(WINDOW_H/ANT_SIZE)
FPS = 100  # 帧率，即每秒刷新多少次
MaxSmell = 100000.0  # 蚂蚁携带的最大信息素
MaxFood = 1000
MaxAnt = 50  # 蚂蚁的个数
MaxBlock = 50  # 障碍物的数目
RandomTurnRate = 0.03  # 蚂蚁随机转弯的概率
AntSight = 3  # 蚂蚁的视力
SmellDropRate = 0.005  # 蚂蚁每次留下多少信息素
AntErrorRate = 0.05  # 蚂蚁要偶尔不要按照原来的路径走，否则会陷入局部解，沿着第一次随机的弯曲路线走
SmellFadeRate = 0.9  # 地面上的信息素随着时间逐步消散的比例，每秒减少到到多少
NULL = -1
HOME_X, HOME_Y = 10, 10  # 窝的位置
FOOD_X = WORLD_W - 10
FOOD_Y = WORLD_H - 10
AntColor = (0, 0, 0)  # 没有食物的蚂蚁，黑色
AntColorwithFood = (128, 0, 128)  # 携带食物的蚂蚁，紫色
BlockColor = (180, 180, 180)  # 障碍物的颜色，灰色
BlackGroundColor = (240, 240, 240)  # 背景颜色，浅灰色
HomeColor = (0, 255, 0)  # 窝，绿色
FoodColor = (0, 0, 255)  # 食物，蓝色
# 运动方向字典
'''directions = {
                '左': (-1, 0), - 0
                '右': (1, 0), - 1
                '上': (0, -1), - 2
                '下': (0, 1), - 3
                '左上': (-1, -1), - 4
                '左下': (-1, 1), - 5
                '右上': (1, -1), - 6
                '右下': (1, 1) - 7
                }'''
directions = ((-1, 0),  # 每一个方向移动的偏移
            (1, 0),
            (0, -1),
            (0, 1),
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1)
            )
TurnBack = (1, 0, 3, 2, 7, 6, 5, 4)  # 往回走对应的方向
# 当前方向可以转弯的4个可能
Turn = ((2, 3, 4, 5), (2, 3, 6, 7), (0, 1, 4, 6), (0, 1, 5, 7), (0, 2, 5, 6), (0, 3, 4, 7), (1, 2, 4, 7), (1, 3, 5, 6))
# ------------- end of 常数定义


class Ant:
    def __init__(self):
        self.x = HOME_X
        self.y = HOME_Y
        self.GotFood = False
        self.Smell = MaxSmell
        self.DirectionNow = random.randrange(8)  # 8个方向的任意一个
        self.__ErrorStepCount = 0

    def RandMove(self):
        if random.random() <= RandomTurnRate:
            self.DirectionNow = Turn[self.DirectionNow][random.randrange(4)]

    def ChooseDirection(self, now, to):  # 有没有更好的方法判断方向？例如查表
        if to[0] == now[0]:
            if to[1] == now[1]:
                return NULL
            elif to[1] > now[1]:
                return 3
            else:
                return 2
        elif to[0] < now[0]:
            if to[1] == now[1]:
                return 0
            elif to[1] > now[1]:
                return 5
            else:
                return 4
        else:
            if to[1] == now[1]:
                return 1
            elif to[1] > now[1]:
                return 7
            else:
                return 6

    def GotoTarget(self, target):
        ddd = self.ChooseDirection((self.x, self.y), (target.x, target.y))
        if ddd != NULL: self.DirectionNow = ddd

    def FindSmell(self, smell):  # 寻找周围最大信息素所在的方向
        TryDir = list(Turn[self.DirectionNow])
        TryDir.append(self.DirectionNow)  # 可以转弯的4个方向加上当前的方向，一共向5个方向尝试
        SmellTop = 0.0  # 记录每一个尝试的方向找到的最大信息素数值
        MaxDir = NULL  # 最大信息素的方向
        for ddd in TryDir:
            xxx, yyy = self.x, self.y
            for i in range(AntSight):
                xxx += directions[ddd][0]
                yyy += directions[ddd][1]
                if self.IsBlock(xxx, yyy): break  # 这个方向走不通，跳过，尝试下一个方向
                #try:
                if smell[yyy][xxx] > SmellTop:
                    SmellTop = smell[yyy][xxx]
                    MaxDir = ddd
                #except IndexError: continue
        if SmellTop <= 1: MaxDir = NULL  # 如果味道太小，按照没有找到处理，随机走，这句话很重要，否则蚂蚁会在原地打圈
        return MaxDir

    def NextStep(self, target, smell):
        AntSightRect = pygame.Rect((self.x - AntSight, self.y - AntSight), (AntSight * 2, AntSight * 2))
        TargetRect = pygame.Rect((target.x - target.size, target.y - target.size), (target.size * 2, target.size * 2))
        if AntSightRect.colliderect(TargetRect):  # 在视野范围内找到终点，直奔终点而去
            self.GotoTarget(target)
        else:  # 否则顺着味道走
            ddd = self.FindSmell(smell)
            if ddd == NULL: self.RandMove()  # 没有找到信息素，随机走
            else:
                if 1<= self.__ErrorStepCount <= AntSight:  # 还在犯错乱走的状态
                    self.RandMove()
                    self.__ErrorStepCount += 1
                else:
                    if self.__ErrorStepCount > AntSight: self.__ErrorStepCount = 0  # 走出了视野范围，重新按照标准算法走
                    if random.random() <= AntErrorRate:
                        self.RandMove()  # 偶尔犯错，乱走
                        self.__ErrorStepCount = 1  # 犯错后不能马上顺着味道走，否则会掉头回去，要先走出蚂蚁的视野，这里启用了一个计数器
                    else:
                        self.DirectionNow = ddd  # 朝着最大信息素的方向走
                        self.__ErrorStepCount = 0

    def IsBlock(self, testx, testy):
        block = False
        # 判断是否碰到边界
        if testx <= 0 or testx >= WORLD_W or testy <= 0 or testy >= WORLD_H:
            block = True
        else:  # 判断是否碰到障碍物。 因为判断两个矩形相交的函数顶部+底部或左侧+右侧边缘除外，所以测试的蚂蚁矩形要向左上角变大一格
            TestRect = pygame.Rect(((testx-1)*ANT_SIZE, (testy-1)*ANT_SIZE), (ANT_SIZE*2, ANT_SIZE*2))
            for bbb in blocks:
                if bbb.colliderect(TestRect):
                    block = True
        return block

    def WaytoTarget(self, target, smell):
        TargetRect = pygame.Rect((target.x - target.size, target.y - target.size), (target.size * 2, target.size * 2))
        if TargetRect.collidepoint(self.x, self.y):
            if self.GotFood:
                self.GotFood = False
                target.FoodNum += 1
            else:
                self.GotFood = True
                target.FoodNum -= 1
            self.Smell = MaxSmell
            self.DirectionNow = random.randrange(8)
        elif self.Smell > 0:  # 没有找到目标，留下味道
            SmellDrop = self.Smell*SmellDropRate
            if SmellDrop > smell[self.y][self.x]: smell[self.y][self.x] = SmellDrop
            self.Smell -= SmellDrop
            if self.Smell < 0: self.Smell = 0.0

    def move(self):
        testx = self.x + directions[self.DirectionNow][0]
        testy = self.y + directions[self.DirectionNow][1]
        if self.IsBlock(testx, testy):  # 如果碰到障碍物或者边界，就试图转弯，转完后还能不能走不要紧，不能走，下一个循环继续尝试转弯，直到找到一个能走的方向为止
            self.DirectionNow = Turn[self.DirectionNow][random.randrange(4)]
        else:
            self.x, self.y = testx, testy
            if self.GotFood: self.WaytoTarget(home, SmellFood)
            else: self.WaytoTarget(food, SmellHome)
            # 这里决定蚂蚁的下一步走向哪里
            if self.GotFood: self.NextStep(home, SmellHome)
            else: self.NextStep(food, SmellFood)


class Home:
    x, y = HOME_X, HOME_Y
    FoodNum = 0
    size = 3


class Food:
    x, y = FOOD_X, FOOD_Y
    FoodNum = MaxFood
    size = 3


# --------------  下面是主程序 和主程序的函数部分  --------------
def BlockInitial1():
    bbb = pygame.Rect((100, 100), (160, 40))
    blocks.append(bbb)
    bbb = pygame.Rect((220, 100), (40, 160))
    blocks.append(bbb)
    bbb = pygame.Rect((500, 200), (40, 300))
    blocks.append(bbb)
    bbb = pygame.Rect((400, 200), (300, 30))
    blocks.append(bbb)


def BlockInitial2():
    bbb = pygame.Rect((1, int(WINDOW_H/2)), (100, 20))
    blocks.append(bbb)
    bbb = pygame.Rect((WINDOW_W-101, int(WINDOW_H/2)), (100, 20))
    blocks.append(bbb)
    bbb = pygame.Rect((int(WINDOW_W/2), 1), (20, 100))
    blocks.append(bbb)
    bbb = pygame.Rect((int(WINDOW_W/2), WINDOW_H-101), (20, 100))
    blocks.append(bbb)


def BlockInitial():
    BlockInitial2()  # 先四边拦一下，避免直接贴边走
    count = 0
    HomeRect = pygame.Rect(((home.x - home.size)*ANT_SIZE, (home.y - home.size)*ANT_SIZE), (home.size * 2*ANT_SIZE, home.size * 2*ANT_SIZE))
    FoodRect = pygame.Rect(((food.x - food.size)*ANT_SIZE, (food.y - food.size)*ANT_SIZE), (food.size * 2*ANT_SIZE, food.size * 2*ANT_SIZE))
    while count < MaxBlock:
        x1, y1 = random.randint(1, WINDOW_W-10), random.randint(1, WINDOW_H-10)
        dx, dy = random.randint(10, int(WINDOW_W/5)), random.randint(10, int(WINDOW_H/5))
        if x1+dx >= WINDOW_W - 1 or y1+dy >= WINDOW_H - 1: continue
        bbb = pygame.Rect((x1, y1), (dx, dy))
        if bbb.colliderect(HomeRect) or bbb.colliderect(FoodRect): continue
        blocks.append(bbb)
        count += 1


def SmellFade():
    for y in range(WORLD_H):
        for x in range(WORLD_W):
            SmellHome[y][x] *= SmellFadeRate
            SmellFood[y][x] *= SmellFadeRate


# 关闭游戏界面
def close_game():
    pygame.quit()
    sys.exit()


# 主函数
def main():
    global display, clock
    pygame.init()
    clock = pygame.time.Clock()
    display = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption('蚁群算法')
    global home, food, blocks
    home = Home()
    food = Food()
    ants = [Ant() for i in range(MaxAnt)]  # i没有用？ 应该有更好的初始化方法 - 这就是标准的用法，列表推导式
    blocks = []
    BlockInitial()
    global SmellHome, SmellFood
    SmellHome = [[0.0 for i in range(WORLD_W)] for i in range(WORLD_H)]
    SmellFood = [[0.0 for i in range(WORLD_W)] for i in range(WORLD_H)]
    SmellFadeCounter = 0
    global FPS
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                close_game()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    close_game()
                elif event.key == K_EQUALS: FPS *= 2  # 加速
                elif event.key == K_MINUS: FPS //= 2  # 减速
                elif event.key == K_z: FPS = 25  # 恢复到正常25帧

        display.fill(BlackGroundColor)
        # 画窝、食物、障碍物、信息素和蚂蚁
        pygame.draw.circle(display, HomeColor, (home.x*ANT_SIZE, home.y*ANT_SIZE), home.size*ANT_SIZE)
        pygame.draw.circle(display, FoodColor, (food.x * ANT_SIZE, food.y * ANT_SIZE), food.size*ANT_SIZE)
        for OneBlock in blocks:
            pygame.draw.rect(display, BlockColor, OneBlock)
        for OneAnt in ants:
            if OneAnt.GotFood: ccc = AntColorwithFood
            else: ccc = AntColor
            pygame.draw.circle(display, ccc, (OneAnt.x*ANT_SIZE, OneAnt.y*ANT_SIZE), ANT_SIZE, 1)
        pygame.display.update()
        pygame.display.set_caption(f'蚁群算法  -  已收集食物{home.FoodNum}，剩余食物{food.FoodNum}， 帧率{FPS}')
        clock.tick(FPS)
        # 蚂蚁走
        for OneAnt in ants:
            OneAnt.move()
        # 味道逐渐消散
        SmellFadeCounter += 1
        if SmellFadeCounter >= FPS:
            SmellFade()
            SmellFadeCounter = 0


if __name__ == '__main__':
    main()
