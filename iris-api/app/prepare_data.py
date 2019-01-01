import itertools,random,json
import numpy as np
import pandas as pd
import requests
from pandas.io.json import json_normalize
from datetime import datetime

def request_url(url,headers,parameter):

    #Accessing the api with accesstoken

    url = url
    headers = headers
    parameter = parameter
    try:
        if parameter:
            r = requests.get(url,headers=headers,params=parameter)
        else:
            r = requests.get(url,headers=headers)
        return r.json()
    except ConnectionError as e:  # This is the correct syntax
        print(e)
        r = "No response"
        return r

def create_seller_info(seller_request):

    #create seller information based on the request json.

    data = seller_request["drugInSale"]
    druginsale = np.array(data) #convert into the numpy ndarray

    #create flattern json so that it can be saved only the requied information into dataframe
    seller_list = []
    for i in druginsale:
        discount = 0
        minimumQuantity = 0
        minAmount = 0
        if "discountForDrug" in i:
            discount = i["discountForDrug"]["discountPercentage"]
            minimumQuantity = i["discountForDrug"]["minimumQuantity"]
            minAmount = i["discountForDrug"]["minimumQuantity"] * i["basePrice"]

        #creating dictionary for each row
        sellerinfo = {
            "id": i["sellerCompany"]["companyName"],
            "price": i["basePrice"],
            "packaging": i["packaging"],
            "isActive": i["isActive"],
            "inventory": i["quantity"],
            "genericName": i["drug"]["genericName"],
            "form": i["drug"]["form"],
            "strength": i["drug"]["strength"],
            "discount": discount,
            "minimumQuantity": minimumQuantity,
            "minAmount": minAmount,
        }
        seller_list.append(sellerinfo)
    df = pd.DataFrame(seller_list) #convert list of dictionary into dataframe
    return df

def create_buyer_info(buyer_request):

    # create buyer information based on the response json.

    data = json_normalize(buyer_request, "orderItems",
                          ["orderDateTime", "currentState", ["buyerUser", "clinicOrDrugStoreName"]])
    #normalize the response json object

    orderlist = data.to_dict('index') #convert the dataframe into dictionary
    eachorderInfo = []

    # creating dictionary for each row
    for i in orderlist:
        order = {
            "id": orderlist[i]['buyerUser.clinicOrDrugStoreName'],
            "quantity": orderlist[i]['quantity'],
            "genericName": orderlist[i]["drugInSales"]["drug"]["genericName"],
            "form": orderlist[i]["drugInSales"]["drug"]["form"],
            "strength": orderlist[i]["drugInSales"]["drug"]["strength"],
            "packaging": orderlist[i]["drugInSales"]["packaging"],
            "orderstatus": orderlist[i]["currentState"],
            "ordertime": orderlist[i]["orderDateTime"],
        }
        eachorderInfo.append(order)

    df = pd.DataFrame(eachorderInfo) #convert it into dataframe
    return df

def search_seller(self):
    
    #get the seller information
    get_seller_url = "http://139.59.255.204:3000/api/DrugInSales/getDrugInSales"
    headers = {'Authorization': 'rMwDAF56oFZV05ohMfUrJ3ipohe5s21bogEF802lmIKZx6Ep65wlHjPjM2uaBfBV'}

    #accessing the api
    get_seller_request = request_url(get_seller_url,headers,None)
    if type(get_seller_request) is not str:
        seller_info = create_seller_info(get_seller_request)        
    return seller_info

def search_buyer(self):
    #get the buyer information

    get_all_order_url = "http://139.59.255.204:3000/api/DrugOrders/getAllOrders"
    get_all_order_parameter = {'from': '2018-09-01', 'to': '2018-10-01'}
    headers = {'Authorization': 'rMwDAF56oFZV05ohMfUrJ3ipohe5s21bogEF802lmIKZx6Ep65wlHjPjM2uaBfBV'}

    #accessing the api
    get_all_order_request = request_url(get_all_order_url,headers,get_all_order_parameter)

    if type(get_all_order_request) is not str:
        buyer_info = create_buyer_info(get_all_order_request)
    return buyer_info


def filter_search_buyer(self,data):
    generic = data["generic"]
    form = data["form"]
    strength = data["strength"]
    package = data["package"]
    orderstatus = data["orderstatus"]
    startdate = data["startdate"]
    enddate = data["enddate"]
    
    # convert the string to date
    start_date = datetime.strptime(startdate,'%Y-%m-%d').date()
    end_date = datetime.strptime(enddate,'%Y-%m-%d').date()
    
    #get buyer data
    buyer = search_buyer(self)
    
    #remove unnecessary character from dataframe packaging column
    buyer['packaging'] = buyer.packaging.str.replace(r'\r\r\n', '')

    #convert the dataframe column ordertime from string to date object
    buyer['ordertime'] = pd.to_datetime(buyer['ordertime']).dt.date
    buyer['orderstatus'] = pd.to_numeric(buyer['orderstatus'])
    
    # check if there is orderstatus for collecting the past data
    if orderstatus:
        buyer_filter = (buyer.genericName.str.contains(generic,regex=False) == True) & (buyer.form.str.contains(form,regex=False) == True) & (buyer.strength.str.contains(strength,regex=False) == True) & (buyer.packaging.str.contains(package,regex=False)== True) & (buyer.orderstatus == orderstatus) & (buyer['ordertime'] > start_date) & (buyer['ordertime'] <= end_date)
    else:
        buyer_filter = (buyer.genericName.str.contains(generic,regex=False) == True) & (buyer.form.str.contains(form,regex=False) == True) & (buyer.strength.str.contains(strength,regex=False) == True) & (buyer.packaging.str.contains(package,regex=False)== True) & (buyer['ordertime'] > start_date) & (buyer['ordertime'] <= end_date)
    
    selected_record = buyer[buyer_filter]
    total_order_quanity=sum(selected_record.quantity.tolist())
    filter_df = selected_record.filter(items=['id', 'quantity'])
    return filter_df,total_order_quanity

def filter_search_seller(self,data):
    generic = data["generic"]
    form = data["form"]
    strength = data["strength"]
    package = data["package"]
    orderstatus = data["orderstatus"]
    startdate = data["startdate"]
    enddate = data["enddate"]
    
    # # convert the string to date
    # start_date = datetime.strptime(startdate,'%Y-%m-%d').date()
    # end_date = datetime.strptime(enddate,'%Y-%m-%d').date()

    #get seller data    
    seller = search_seller(self)

    seller['packaging'] = seller.packaging.str.replace(r'\r\r\n', '')
    seller_filer = (seller.genericName.str.contains(generic,regex=False) == True)& (seller.form.str.contains(form,regex=False) == True) & (seller.strength.str.contains(strength,regex=False) == True) & (seller.packaging.str.contains(package,regex=False) == True) & (seller.discount != 0 )
    selected_seller_record = seller[seller_filer]
    total_inventory_quantity = sum(selected_seller_record.inventory.tolist())
    filter_seller_df = selected_seller_record.filter(items=['id','price','minAmount','discount','inventory'])

    return filter_seller_df,total_inventory_quantity    

def filter_search(self,data):

    filter_df,total_order_quanity = filter_search_buyer(self,data)
    buyer_filter = filter_df.groupby('id', as_index=False).agg({"quantity": "sum"})

    filter_seller_df,total_inventory_quantity = filter_search_seller(self,data)
    
    result_data = {
        'buyers': buyer_filter.to_json(),
        'BIQ': total_order_quanity,
        'sellers': filter_seller_df.to_json(),
        'SIQ':total_inventory_quantity,
    }
    return result_data


