from django.http import HttpResponse
from django.shortcuts import render
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from datetime import datetime, date, timedelta
from flask_login import LoginManager
login_manager = LoginManager()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///todo.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#this model is used for customer details(only name and contact number)
class Todo(db.Model):
    __tablename__ = 'todo'
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"{self.title}"

#this model is used for cutomer purchase details
class PurchaseDetails(db.Model):
    __tablename__ = 'purchase_details'
    id = db.Column(db.Integer, primary_key=True)
    product_name=db.Column(db.String(200), nullable=False)
    total_price = db.Column(db.Integer, nullable=False)
    paid_price = db.Column(db.Integer, nullable=False)
    remain_price = db.Column(db.Integer, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('todo.sno'),
                             nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"{self.product_name}"        


@app.route('/latest')
def latest():
    temptodo = Todo.query.order_by(Todo.date_created.desc()).all() 
    return render_template('index.html', allTodo=temptodo) 

@app.route('/latest/5')
def latest_5():
    temptodo = Todo.query.order_by(Todo.date_created.desc()).limit(5).all() 
    return render_template('index.html', allTodo=temptodo)

@app.route('/oldest')
def oldest():
    temptodo = Todo.query.order_by(Todo.date_created.asc()).all() 
    return render_template('index.html', allTodo=temptodo) 

@app.route('/oldest/5')
def oldest_5():
    temptodo = Todo.query.order_by(Todo.date_created.asc()).limit(5).all() 
    return render_template('index.html', allTodo=temptodo)     

@app.route('/bytitle')
def by_title():
    temptodo = Todo.query.order_by(Todo.title.desc()).all() 
    return render_template('index.html', allTodo=temptodo)  
                
@app.route('/login/')
def login():
    return render_template('login.html')

@app.route('/', methods=['GET', 'POST'])
def hello_world():
    if request.method=='POST':
        title = request.form['title']
        desc = request.form['desc']
        todo = Todo(title=title, desc=desc)
        db.session.add(todo)
        db.session.commit()

    temptodo = Todo.query.order_by(Todo.title.asc()).all()
    return render_template('index.html', allTodo=temptodo)

@app.route('/business/overview')
def business_overview():
    total_sales = PurchaseDetails.query.with_entities(
             func.sum(PurchaseDetails.total_price)).first()   
    total_sales =total_sales[0]

    paid_sales = PurchaseDetails.query.with_entities(
             func.sum(PurchaseDetails.paid_price)).first()   
    paid_sales =paid_sales[0]

    remain_payment_sales =total_sales-paid_sales
    sales_detail = [total_sales, paid_sales, remain_payment_sales]
                                                                              
    per_customer_sale = PurchaseDetails.query.with_entities(
             func.sum(PurchaseDetails.total_price),
             func.sum(PurchaseDetails.paid_price), 
             func.sum(PurchaseDetails.remain_price),
             PurchaseDetails.customer_id,
             func.count(PurchaseDetails.customer_id)
             ).group_by(PurchaseDetails.customer_id).all()
    customer_list = []
    today_sales = PurchaseDetails.query.filter(
        func.date(PurchaseDetails.date_created)==date.today()-timedelta(days=0)).all()
    yesterday_sales = PurchaseDetails.query.filter(
        func.date(PurchaseDetails.date_created)==date.today()-timedelta(days=1)).all()
    week_sales = PurchaseDetails.query.filter(
        func.date(PurchaseDetails.date_created)>date.today()-timedelta(days=7)).all()
    month_sales = PurchaseDetails.query.filter(
        func.date(PurchaseDetails.date_created)>date.today()-timedelta(days=30)).all()
    quarter_sales = PurchaseDetails.query.filter(
        func.date(PurchaseDetails.date_created)>date.today()-timedelta(days=180)).all()
    year_sales = PurchaseDetails.query.filter(
        func.date(PurchaseDetails.date_created)>date.today()-timedelta(days=365)).all()
    sales_data = [  today_sales,
                    yesterday_sales,
                    week_sales,
                    month_sales,
                    quarter_sales,
                    year_sales ]
    for customer in per_customer_sale:
        customer = list(customer)
        user = Todo.query.filter_by(sno=customer[3]).first()
        print(user)
        customer.append(user.title)
        customer.append(user.desc)
        customer_list.append(customer)
    return render_template('business.html',
                            sales_detail=sales_detail,
                            per_customer_sale=customer_list,
                            sales_data= sales_data)

@app.route('/search', methods=['GET', 'POST'])
def filter_data():
    if request.method == 'POST':
        print("inside post method")
        value =request.form['inputvalue']
        print(value)
        temptodo=Todo.query.filter(Todo.title.startswith(value)).all()
        return render_template('index.html', allTodo=temptodo) 

    temptodo = Todo.query.order_by(Todo.title.asc()).all()
    return render_template('index.html', allTodo=temptodo)    

@app.route('/show')
def products():
    allTodo = Todo.query.all()
    
    return 'this is products page'

@app.route('/view/<int:sno>')
def view(sno):
    todo = Todo.query.filter_by(sno=sno).first()
    print(todo)
    product_list = PurchaseDetails.query.filter_by(customer_id =sno).all()
    sum =0
    for i in product_list:
        sum+=i.remain_price
      

    total_remain_price = db.select([db.func.sum(PurchaseDetails.remain_price)])
    print(total_remain_price)
    
    return render_template('view.html',product_list=product_list, todo=todo, sum=sum)

@app.route('/update/<int:sno>', methods=['GET', 'POST'])
def update(sno):
    if request.method=='POST':
        item = request.form['item']
        total_price = request.form['totalprice']
        paid_amount = request.form['paidamount']
        remain_amount = int(total_price)-int(paid_amount)
        purchase_detail = PurchaseDetails(product_name=item,
                                            total_price=total_price,
                                            paid_price=paid_amount,
                                            remain_price=remain_amount,
                                            customer_id=sno
                                            )
        db.session.add(purchase_detail)
        db.session.commit()
        return redirect('/')
       
    todo = Todo.query.filter_by(sno=sno).first()
    return render_template('update.html', todo=todo)

@app.route('/delete/<int:sno>')
def delete(sno):
    todo = Todo.query.filter_by(sno=sno).first()
    print(todo)
    db.session.delete(todo)
    db.session.commit()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True, port=8000)