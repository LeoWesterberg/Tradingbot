from numpy import double, empty
from pandas.core.frame import DataFrame
from DbManagement import DbManagement
from Constants import Constants as const
import datetime
from OrderManagement import OrderManagement
from scipy.signal import find_peaks



class NewAlgorithms:
    
    def __init__(self, db:DbManagement):
        self.db = db 
        self.order_management:OrderManagement = OrderManagement()



    def retrieveValue(self, df:DataFrame, attr:str):
        return df[attr].to_list()[0]



    def retrieve_value_dt(self, dt, attr:str):
        return self.db.get_row_at_date(dt)[attr].to_list()[0]



    def attr1_over_attr2(self, attrOver, attrUnder, dt):    
        current_attr_over = self.retrieve_value_dt(dt,attrOver)
        current_attr_under = self.retrieve_value_dt(dt,attrUnder)
        
        return current_attr_over > current_attr_under



    def macd_crossover(self, dt):
        previous_date = self.get_previous_date(dt)
        prev_macd_stat = self.attr1_over_attr2(const.MACD_INDEX,const.SIGNAL_INDEX,previous_date)
        current_macd_stat = self.attr1_over_attr2(const.MACD_INDEX,const.SIGNAL_INDEX,dt) 
        
        return current_macd_stat and not prev_macd_stat


    
    def signal_crossover(self, dt):
        previous_date = self.get_previous_date(dt)
        prev_macd_stat = self.attr1_over_attr2(const.SIGNAL_INDEX,const.MACD_INDEX,previous_date)
        current_macd_stat = self.attr1_over_attr2(const.SIGNAL_INDEX,const.MACD_INDEX,dt) 
        
        return current_macd_stat and not prev_macd_stat
    


    def attr_secant(self,dt,attr,window):
        prev_date = self.get_previous_date(dt)

        for i in range(1,window):
            prev_date = self.get_previous_date(prev_date)

        return self.retrieve_value_dt(dt,attr) - self.retrieve_value_dt(prev_date,attr)



    def macd_under_zero_line(self,dt):
        return self.retrieve_value_dt(dt,const.MACD_INDEX) < 0



    def get_previous_date(self,dt):
        previousIndex = self.retrieve_value_dt(dt,const.INDEX)  - 1     
        
        return self.retrieveValue(self.db.get_row_at_index(previousIndex),const.DATETIME)



    def short_long_ema_cross(self,dt:datetime): #check
        previous_date = self.get_previous_date(dt)
        curr_ema_stat = self.attr1_over_attr2(const.EMA_Short_INDEX,const.EMA_Long_INDEX,dt)
        prev_ema_stat = self.attr1_over_attr2(const.EMA_Short_INDEX,const.EMA_Long_INDEX,previous_date)
        
        return curr_ema_stat and not prev_ema_stat


    def all_pullback_indicies(self):
        data = self.db.get_table()
        smooth_closings = data[const.EMA_Short_INDEX].values
        
        return find_peaks(-smooth_closings,distance=5,prominence=self.retrieveValue(self.db.get_previous_row(),const.CLOSE_INDEX) * 0.001)[0]
    


    def recent_pullback_value(self,dt,search_range):
        data = self.db.get_row_at_date(dt)

        for i in range(search_range):
            dt = self.get_previous_date(dt)
            data = data.append(self.db.get_row_at_date(dt))

        data = data.iloc[::-1]  
        smooth_closings = data[const.CLOSE_INDEX].values
        nearby_peaks = find_peaks(-smooth_closings,distance=10,prominence=self.retrieveValue(self.db.get_row_at_date(dt),const.CLOSE_INDEX) * 0.001)[0]
       
        return -1 if len(nearby_peaks) == 0 else ([data[const.CLOSE_INDEX].to_list()[i] for i in nearby_peaks][-1])


        
    def buy_signal(self,dt):
        gen_trend_condition = self.attr1_over_attr2(const.EMA_Short_INDEX,const.EMA_200_INDEX,dt)
        macd_condition = self.macd_crossover(dt) and self.macd_under_zero_line(dt)
        
        return gen_trend_condition and macd_condition # and local_trend_condition):



    def sell_signal(self,dt,stop_loss,take_profit):
        current_close = self.retrieve_value_dt(dt,const.CLOSE_INDEX)
        
        return current_close >= take_profit or current_close <= stop_loss #or dt.hour == 21 and dt.minute == 60-const.TICKER_INTERVAL



    def __initialize_sell_order(self, order_id) -> None:
        self.order_management.sell_order(order_id)
        


    def __initialize_buy_order(self, dt, current_close:float) -> None:
        stop_loss = self.retrieve_value_dt(dt,const.EMA_200_INDEX) #if (stop_loss == -1 or stop_loss < current_close) else stop_loss  
        risk = current_close - stop_loss
        take_profit = current_close + risk * const.RR_RATIO
        self.order_management.buy_order(stop_loss, take_profit)



    def strategy(self, dt):
        current_close = self.retrieve_value_dt(dt,const.CLOSE_INDEX)

        if(self.buy_signal(dt)):
            self.__initialize_buy_order(dt,current_close)

        for index, row in self.order_management.current_holdings.iterrows():
            if(self.sell_signal(dt,row["Stop loss"],row["Profit take"])):
                self.__initialize_sell_order(row["Order id"])
                
            
            


            


    

    

