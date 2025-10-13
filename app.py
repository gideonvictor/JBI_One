import sys
import pymysql
import logging
import traceback

from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from config import postgres_username, postgres_password, postgres_host, postgres_port, postgres_dbname

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+mysqldb://{postgres_username}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_dbname}"
)
db = SQLAlchemy(app)
logging.basicConfig(format="%(levelname)s - %(name)s - %(message)s", level=logging.INFO, stream=sys.stdout)
log = logging.getLogger(__name__)

def clean_value(val):
    if val is None or val == "" or str(val).lower() == "none":
        return None
    return val

class jobs_index(db.Model):
    job_id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(200), nullable=True)
    account = db.Column(db.String(200), nullable=True)
    jbi_number = db.Column(db.String(200), nullable=True)
    market = db.Column(db.String(200), nullable=True)
    purchase_amount = db.Column(db.String(200), nullable=True)
    commission_at_sale = db.Column(db.String(200), nullable=True)
    commission_net_due = db.Column(db.String(200), nullable=True)
    
    def __repr__(self):
        return '<Task %r>' % self.id
    
class jobs(db.Model):
    job_id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(200), nullable=True)
    
    def __repr__(self):
        return '<Task %r>' % self.id
    
class jobs_detail(db.Model):
    job_id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(200), nullable=True)
    account = db.Column(db.String(200), nullable=True)
    reference_contact = db.Column(db.String(200), nullable=True)
    phone_number = db.Column(db.String(200), nullable=True)
    equipment_description = db.Column(db.String(200), nullable=True)
    jbi_number = db.Column(db.String(200), nullable=True)
    market = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(200), nullable=True)
    contractor_id = db.Column(db.String(200), nullable=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    ship_date = db.Column(db.DateTime, default=datetime.utcnow)
    complete = db.Column(db.String(200), nullable=True)
    judy_task = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return '<Task %r>' % self.id

class engineer_detail(db.Model):
    job_id = db.Column(db.Integer, primary_key=True)
    engineer_id = db.Column(db.Integer, primary_key=True)
    engineer_name = db.Column(db.String(200), primary_key=True)
    engineer_contact = db.Column(db.String(200), nullable=True)
    engineer_phone = db.Column(db.String(200), nullable=True)
    
    def __repr__(self):
        return '<Task %r>' % self.id

class sales_detail(db.Model):
    job_id = db.Column(db.Integer, primary_key=True)
    sales_name = db.Column(db.String(200), primary_key=True)
    sales_contact = db.Column(db.String(200), nullable=True)
    sales_phone = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return '<Task %r>' % self.id
    
class job_engineer(db.Model):
    job_id = db.Column(db.Integer, primary_key=True)
    engineer_id = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        return '<Task %r>' % self.id
    
class jobs_sales(db.Model):
    job_id = db.Column(db.Integer, primary_key=True)
    sales_id = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        return '<Task %r>' % self.id

class engineer(db.Model):
    engineer_id = db.Column(db.Integer, primary_key=True)
    engineer_name = db.Column(db.String(200), nullable=True)
    engineer_contact = db.Column(db.String(200), nullable=True)
    engineer_phone = db.Column(db.String(200), nullable=True)
    def __repr__(self):
        return '<Task %r>' % self.id

class sales(db.Model):
    sales_id = db.Column(db.Integer, primary_key=True)
    sales_name = db.Column(db.String(200), nullable=True)
    sales_contact = db.Column(db.String(200), nullable=True)
    sales_phone = db.Column(db.String(200), nullable=True)
    def __repr__(self):
        return '<Task %r>' % self.id



@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        try:
            # Use SQLAlchemy to get the max job_id safely
            id = db.session.query(func.max(jobs.job_id)).scalar() or 0
            id += 1

            new_task = jobs(
                job_id=id,
                project_name=request.form.get('job')
            )

            db.session.add(new_task)
            db.session.commit()

            return redirect('/')
        except Exception as e:
            db.session.rollback()
            error_message = traceback.format_exc()
            log.error(error_message)
            print(error_message)
            return f"There was an issue adding your task: {str(e)}"
    else:
        try:
            tasks = jobs_index.query.order_by(jobs_index.job_id).all()
            return render_template('index.html', tasks=tasks)
        except Exception as e:
            error_message = traceback.format_exc()
            log.error(error_message)
            print(error_message)
            return "Error loading index page"


@app.route('/detail/<int:job_id>', methods=['GET', 'POST'])
def detail(job_id):
    tasks = jobs_detail.query.get_or_404(job_id)
    engineers = engineer_detail.query.filter_by(job_id=job_id).all()
    all_engineers = engineer.query.all()
    sales_details = sales_detail.query.filter_by(job_id=job_id).all()
    all_sales = sales.query.all()
    error_message = traceback.format_exc()
    log.error(error_message)
    print(error_message)
    return render_template('detail.html', tasks=tasks, engineers=engineers, sales_details=sales_details, all_engineers=all_engineers, all_sales=all_sales)

@app.route('/detail/<int:job_id>/edit', methods=['GET', 'POST'])
def header_to_edit(job_id):
    header_to_edit = jobs_detail.query.get_or_404(job_id)
    engineers = engineer.query.all()
    if request.method == 'POST':
        header_to_edit.project_name = clean_value(request.form.get('project_name', header_to_edit.project_name))
        header_to_edit.account = clean_value(request.form.get('account', header_to_edit.account))
        # header_to_edit.engineer_id = request.form.get('engineer_id', header_to_edit.engineer_id)
        header_to_edit.reference_contact = clean_value(request.form.get('reference_contact', header_to_edit.reference_contact))
        header_to_edit.phone_number = clean_value(request.form.get('phone_number', header_to_edit.phone_number))
        header_to_edit.equipment_description = clean_value(request.form.get('equipment_description', header_to_edit.equipment_description))
        header_to_edit.jbi_number = clean_value(request.form.get('jbi_number', header_to_edit.jbi_number))
        header_to_edit.market = clean_value(request.form.get('market', header_to_edit.market))
        header_to_edit.status = clean_value(request.form.get('status', header_to_edit.status))
        header_to_edit.contractor_id = clean_value(request.form.get('contractor_id', header_to_edit.contractor_id))
        header_to_edit.order_date = clean_value(request.form.get('order_date', header_to_edit.order_date))
        header_to_edit.ship_date = clean_value(request.form.get('ship_date', header_to_edit.ship_date))
        header_to_edit.complete = clean_value(request.form.get('complete', header_to_edit.complete))
        header_to_edit.judy_task = clean_value(request.form.get('judy_task', header_to_edit.judy_task))
        try:
            db.session.commit()
            return redirect(f'/detail/{job_id}')
        except Exception as e:
            error_message = traceback.format_exc()
            log.debug(error_message)
            print(error_message)
            db.session.rollback()
            return 'There was an issue updating the header'
    else:
        tasks = jobs_detail.query.get_or_404(job_id)
        sales = sales_detail.query.filter_by(job_id=job_id).all()
        error_message = traceback.format_exc()
        log.error(error_message)
        print(error_message)
        return render_template('detail_edit_job.html', tasks=tasks, engineers=engineers, sales=sales)
    
@app.route('/detail/<int:job_id>/edit_engineer', methods=['POST'])
def job_engineer_edit(job_id):
    print("POST received for job_id:", job_id)
    engineer_name = request.form.get('engineer_name')
    engineer_obj = engineer.query.filter_by(engineer_name=engineer_name).first()
    if not engineer_obj:
        return 'Engineer not found', 400

    # Check if this job-engineer pair already exists to avoid duplicates
    existing = job_engineer.query.filter_by(job_id=job_id, engineer_id=engineer_obj.engineer_id).first()
    if not existing:
        new_job_engineer = job_engineer(job_id=job_id, engineer_id=engineer_obj.engineer_id)
        db.session.add(new_job_engineer)
        try:
            db.session.commit()
            return redirect(f'/detail/{job_id}')
        except Exception as e:
            db.session.rollback()
            error_message = traceback.format_exc()
            log.debug(error_message)
            print(error_message)
            return 'There was an issue updating the job engineer'
    else:
        # Already exists, just redirect
        return redirect(f'/detail/{job_id}')

@app.route('/detail/<int:job_id>/edit_sales', methods=['POST'])
def job_sales_edit(job_id):
    print("POST received for sales_id:")
    sales_name = request.form.get('sales_name')
    sales_obj = sales.query.filter_by(sales_name=sales_name).first()
    if not sales_obj:
        return 'Sales not found', 400

    # Check if this job-sales pair already exists to avoid duplicates
    existing = jobs_sales.query.filter_by(job_id=job_id, sales_id=sales_obj.sales_id).first()
    if not existing:
        new_job_sales = jobs_sales(job_id=job_id, sales_id=sales_obj.sales_id)
        db.session.add(new_job_sales)
        try:
            db.session.commit()
            return redirect(f'/detail/{job_id}')
        except Exception as e:
            db.session.rollback()
            error_message = traceback.format_exc()
            log.debug(error_message)
            print(error_message)
            return 'There was an issue updating the job engineer'
    else:
        # Already exists, just redirect
        return redirect(f'/detail/{job_id}')

if __name__ == "__main__":
    app.run(debug=True)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()
