from flask import Flask, render_template, request, redirect, url_for
from models import db, Invoice
from sqlalchemy import func
import os
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "hjshjhdjahkjyytoldhjsyj"

db.init_app(app)

# Admin Panel for managing invoices
admin = Admin(app, name="POS Admin", template_mode="bootstrap3")
admin.add_view(ModelView(Invoice, db.session))


# Home page
@app.route('/')
def index():
    # Fetch the last 5 entries ordered by date or ID descending
    invoices = Invoice.query.order_by(Invoice.id.desc()).limit(5).all()
    return render_template('dashboard.html', invoices=invoices)

# Add new invoice
@app.route('/add_invoice', methods=['GET', 'POST'])
def add_invoice():
    if request.method == 'POST':
        name = request.form['customer_name']
        service = request.form['service']
        amount = request.form['amount']
        
        new_invoice = Invoice(customer_name=name, service=service, amount=float(amount))
        db.session.add(new_invoice)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_invoice.html')

@app.route('/view_invoices')
def view_invoices():
    invoices = Invoice.query.all()
    return render_template('view_invoices.html', invoices=invoices)

@app.route('/print_invoice/<int:invoice_id>')
def print_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template('print_invoice.html', invoice=invoice)

@app.route('/view_reports', methods=['GET'])
def view_reports():
    # Get filter parameter from the URL (default to 'daily')
    filter_type = request.args.get('filter', 'daily')

    # Initialize an empty list to store report data
    reports = []

    # Filter logic for daily, weekly, and monthly
    if filter_type == 'daily':
        # Group by date
        results = (
            db.session.query(
                func.date(Invoice.date).label("period"),
                func.count(Invoice.id).label("invoice_count"),
                func.sum(Invoice.amount).label("total_revenue")
            )
            .group_by(func.date(Invoice.date))
            .all()
        )
    elif filter_type == 'weekly':
        # Group by week
        results = (
            db.session.query(
                func.strftime('%Y-%W', Invoice.date).label("period"),
                func.count(Invoice.id).label("invoice_count"),
                func.sum(Invoice.amount).label("total_revenue")
            )
            .group_by(func.strftime('%Y-%W', Invoice.date))
            .all()
        )
    elif filter_type == 'monthly':
        # Group by month
        results = (
            db.session.query(
                func.strftime('%Y-%m', Invoice.date).label("period"),
                func.count(Invoice.id).label("invoice_count"),
                func.sum(Invoice.amount).label("total_revenue")
            )
            .group_by(func.strftime('%Y-%m', Invoice.date))
            .all()
        )

    # Format results for the template
    for row in results:
        reports.append({
            "period": row.period,
            "invoice_count": row.invoice_count,
            "total_revenue": row.total_revenue or 0
        })

    # Render the reports template
    return render_template('view_reports.html', reports=reports, filter=filter_type)

if __name__ == '__main__':
    with app.app_context():
        if not os.path.exists('database.db'):
            db.create_all()
    app.run(debug=True)
