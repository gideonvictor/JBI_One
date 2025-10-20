import os
import sys
import logging
import traceback
from datetime import datetime

import pymysql
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

from config import (
    postgres_username,
    postgres_password,
    postgres_host,
    postgres_port,
    postgres_dbname,
)

# -----------------------------------------------------------------------------
# Flask + SQLAlchemy setup
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+mysqldb://{postgres_username}:{postgres_password}@"
    f"{postgres_host}:{postgres_port}/{postgres_dbname}"
)
db = SQLAlchemy(app)

# Logging
logging.basicConfig(
    format="%(levelname)s - %(name)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Utility helpers
# -----------------------------------------------------------------------------
def clean_value(val):
    """Normalize empty values to None."""
    if val is None or val == "" or str(val).lower() == "none":
        return None
    return val


def _to_float(v):
    """Safe conversion to float with fallback to 0.0."""
    try:
        return float(v) if v not in (None, "") else 0.0
    except Exception:
        return 0.0


def get_job_totals(job_id):
    """
    Fetch purchase and commission totals for a given job_id from jobs_index.
    Returns a dict with the same keys used by detail_tiles.html.
    """
    job_index_entry = jobs_index.query.filter_by(job_id=job_id).first()
    if not job_index_entry:
        return {k: 0.0 for k in ["purchase_amount", "commission_at_sale", "commission_net_due"]}
    return {
        "purchase_amount": _to_float(job_index_entry.purchase_amount),
        "commission_at_sale": _to_float(job_index_entry.commission_at_sale),
        "commission_net_due": _to_float(job_index_entry.commission_net_due),
    }


# -----------------------------------------------------------------------------
# SQLAlchemy Models
# -----------------------------------------------------------------------------
class commission_detail_line(db.Model):
    job_id = db.Column(db.Integer)
    commission_id = db.Column(db.Integer)
    commission_line_id = db.Column(db.Integer, primary_key=True)
    commission_amount = db.Column(db.String(200))
    date_commission = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CommissionDetailLine {self.commission_line_id}>"


class engineer(db.Model):
    engineer_id = db.Column(db.Integer, primary_key=True)
    engineer_name = db.Column(db.String(200))
    engineer_contact = db.Column(db.String(200))
    engineer_phone = db.Column(db.String(200))

    def __repr__(self):
        return f"<Engineer {self.engineer_name}>"


class engineer_detail(db.Model):
    auto_id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer)
    engineer_id = db.Column(db.Integer)
    engineer_name = db.Column(db.String(200))
    engineer_contact = db.Column(db.String(200))
    engineer_phone = db.Column(db.String(200))

    def __repr__(self):
        return f"<EngineerDetail {self.job_id}:{self.engineer_name}>"


class jobs(db.Model):
    job_id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(200))

    def __repr__(self):
        return f"<Job {self.job_id}>"


class jobs_commission(db.Model):
    commission_id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer)
    purchase_amount = db.Column(db.String(200))
    commission_at_sale = db.Column(db.String(200))
    commission_due_pct = db.Column(db.String(200))
    commission_adjust = db.Column(db.String(200))
    cause_of_adjustment = db.Column(db.String(200))
    commission_net_due = db.Column(db.String(200))
    notes = db.Column(db.String(2000))
    final_commission = db.Column(db.String(200))
    final_due = db.Column(db.String(200))
    commission_due_1 = db.Column(db.String(200))
    du1_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<JobsCommission {self.commission_id}>"


class jobs_commission_line(db.Model):
    commission_id = db.Column(db.Integer)
    commission_line_id = db.Column(db.Integer, primary_key=True)
    commission_amount = db.Column(db.String(200))
    date_commission = db.Column(db.Date, default=datetime.utcnow)

    def __repr__(self):
        return f"<JobsCommissionLine {self.commission_line_id}>"


class jobs_detail(db.Model):
    job_id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(200))
    account = db.Column(db.String(200))
    reference_contact = db.Column(db.String(200))
    phone_number = db.Column(db.String(200))
    equipment_description = db.Column(db.String(200))
    jbi_number = db.Column(db.String(200))
    market = db.Column(db.String(200))
    status = db.Column(db.String(200))
    contractor = db.Column(db.String(200))
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    ship_date = db.Column(db.DateTime, default=datetime.utcnow)
    complete = db.Column(db.String(200))
    judy_task = db.Column(db.String(200))

    def __repr__(self):
        return f"<JobsDetail {self.job_id}>"


class job_engineer(db.Model):
    auto_id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer)
    engineer_id = db.Column(db.Integer)

    def __repr__(self):
        return f"<JobEngineer {self.job_id}:{self.engineer_id}>"


class jobs_index(db.Model):
    job_id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(200))
    account = db.Column(db.String(200))
    jbi_number = db.Column(db.String(200))
    market = db.Column(db.String(200))
    contractor = db.Column(db.String(200))
    purchase_amount = db.Column(db.String(200))
    commission_at_sale = db.Column(db.String(200))
    commission_net_due = db.Column(db.String(200))

    def __repr__(self):
        return f"<JobsIndex {self.job_id}>"


class jobs_sales(db.Model):
    auto_id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer)
    sales_id = db.Column(db.Integer)
    job_percentage = db.Column(db.String(200))

    def __repr__(self):
        return f"<JobsSales {self.job_id}:{self.sales_id}>"


class sales(db.Model):
    sales_id = db.Column(db.Integer, primary_key=True)
    sales_name = db.Column(db.String(200))
    sales_contact = db.Column(db.String(200))
    sales_phone = db.Column(db.String(200))

    def __repr__(self):
        return f"<Sales {self.sales_name}>"


class sales_detail(db.Model):
    auto_id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer)
    sales_name = db.Column(db.String(200))
    sales_contact = db.Column(db.String(200))
    sales_phone = db.Column(db.String(200))
    job_percentage = db.Column(db.String(200))


    def __repr__(self):
        return f"<SalesDetail {self.auto_id}:{self.auto_id}>"

    
def _to_float(v):
                try:
                    if v is None or v == "":
                        return 0.0
                    return float(v)
                except Exception:
                    return 0.0
    
def get_job_totals(job_id):
    """
    Fetch purchase and commission totals for a given job_id from jobs_index.
    Returns a dict with the same keys used by detail_tiles.html.
    """
    job_index_entry = jobs_index.query.filter_by(job_id=job_id).first()

    if not job_index_entry:
        return {
            "purchase_amount": 0.0,
            "commission_at_sale": 0.0,
            "commission_net_due": 0.0,
        }

    return {
        "purchase_amount": _to_float(job_index_entry.purchase_amount),
        "commission_at_sale": _to_float(job_index_entry.commission_at_sale),
        "commission_net_due": _to_float(job_index_entry.commission_net_due),
    }

@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        try:
            job_id = (db.session.query(func.max(jobs.job_id)).scalar() or 0) + 1
            db.session.add_all([jobs(job_id=job_id), jobs_commission(job_id=job_id)])
            db.session.commit()
            return redirect(f"/detail/{job_id}/edit")
        except Exception as e:
            db.session.rollback()
            log.exception("Error adding new job")
            return f"There was an issue adding your task: {str(e)}"

    try:
        q = jobs_index.query
        filters = {
            "project_name": request.args.get("project_name", type=str),
            "account": request.args.get("account", type=str),
            "jbi_number": request.args.get("jbi_number", type=str),
            "market": request.args.get("market", type=str),
            "contractor": request.args.get("contractor", type=str),
        }
        for field, value in filters.items():
            if value:
                q = q.filter(getattr(jobs_index, field).ilike(f"%{value}%"))

        jobs_summary = q.order_by(jobs_index.job_id).all()
        job_detail_totals = {
            "purchase_amount": sum(_to_float(js.purchase_amount) for js in jobs_summary),
            "commission_at_sale": sum(_to_float(js.commission_at_sale) for js in jobs_summary),
            "commission_net_due": sum(_to_float(js.commission_net_due) for js in jobs_summary),
        }
        return render_template("index.html", jobs_summary=jobs_summary, job_detail_totals=job_detail_totals, filters=request.args)
    except Exception:
        log.exception("Error loading index page")
        return "Error loading index page"

@app.route('/detail/<int:job_id>/commission_line', methods=['POST'])
def commission_line(job_id):
    commission_line_amount = request.form.get('commission_amount')
    commission_line_date = request.form.get('date')
    parent_commission_id = jobs_commission.query.filter_by(job_id=job_id).first().commission_id
    new_commission = jobs_commission_line(
        commission_amount=commission_line_amount,
        date_commission=commission_line_date,
        commission_id=parent_commission_id,
    )
    try:
        db.session.add(new_commission)
        db.session.commit()
        return redirect(f'/detail/{job_id}')
    except Exception as e:
        db.session.rollback()
        error_message = traceback.format_exc()
        log.debug(error_message + str(e))
        print(error_message + str(e))
        return 'There was an issue updating the commission line information'
    
@app.route("/detail/<int:job_id>", methods=["GET"])
def detail(job_id):
    """View job detail page (read-only)."""
    try:
        job_detail = jobs_detail.query.get_or_404(job_id)
        jobs_summary = jobs_index.query.order_by(jobs_index.job_id).all()
        job_detail_totals = get_job_totals(job_id)

        eng = engineer_detail.query.filter_by(job_id=job_id).all()
        sales_details_for_job = sales_detail.query.filter_by(job_id=job_id).all()  # ✅ includes auto_id now
        parent_commission = jobs_commission.query.filter_by(job_id=job_id).first()
        commission_lines = commission_detail_line.query.filter_by(job_id=job_id).all()

        return render_template(
            "detail.html",
            job_detail=job_detail,
            job_detail_totals=job_detail_totals,
            jobs_summary=jobs_summary,
            eng=eng,
            sales_details_for_job=sales_details_for_job,
            engineers_list=engineer.query.all(),
            sales_list=sales.query.all(),
            parent_commission_id=parent_commission,
            commission_lines_for_job=commission_lines,
        )

    except Exception:
        log.exception(f"Error loading detail page for job_id={job_id}")
        return "There was an issue gathering details on the job", 500

@app.route("/detail/<int:job_id>/edit", methods=["GET", "POST"])
def detail_edit(job_id):
    """Edit job detail information."""
    job_detail = jobs_detail.query.get_or_404(job_id)
    jobs_summary = jobs_index.query.order_by(jobs_index.job_id).all()
    job_detail_totals = get_job_totals(job_id)

    eng = engineer_detail.query.filter_by(job_id=job_id).all()
    parent_commission = jobs_commission.query.filter_by(job_id=job_id).first()
    sales_details_for_job = sales_detail.query.filter_by(job_id=job_id).all()
    commission_lines = commission_detail_line.query.filter_by(job_id=job_id).all()

    if request.method == "POST":
        try:
            # Update all editable fields using a loop
            editable_fields = [
                "project_name", "account", "reference_contact", "phone_number",
                "equipment_description", "jbi_number", "market", "status",
                "contractor", "order_date", "ship_date", "complete", "judy_task",
            ]
            for field in editable_fields:
                setattr(job_detail, field, clean_value(request.form.get(field, getattr(job_detail, field))))

            db.session.commit()
            return redirect(f"/detail/{job_id}")

        except Exception:
            db.session.rollback()
            log.exception(f"Error updating job detail for job_id={job_id}")
            return "There was an issue updating the header", 500

    # GET request: render edit page
    return render_template(
        "detail_edit_job.html",
        job_detail=job_detail,
        job_detail_totals=job_detail_totals,
        jobs_summary=jobs_summary,
        eng=eng,
        sales_details_for_job=sales_details_for_job,
        engineers_list=engineer.query.all(),
        sales_list=sales.query.all(),
        parent_commission_id=parent_commission,
        commission_lines_for_job=commission_lines,
    )

@app.route('/engineers', methods=['GET', 'POST'])
def engineers():
    engineers_list = engineer.query.all()
    if request.method == 'POST':
        engineer_name = request.form.get('engineer_name')
        engineer_contact = request.form.get('engineer_contact')
        engineer_phone = request.form.get('engineer_phone')
        new_engineer = engineer(
            engineer_name=engineer_name,
            engineer_contact=engineer_contact,
            engineer_phone=engineer_phone
        )
        try:
            db.session.add(new_engineer)
            db.session.commit()
            return redirect('/engineers')
        except Exception as e:
            db.session.rollback()
            error_message = traceback.format_exc()
            log.debug(error_message + str(e))
            print(error_message + str(e))
            return 'There was an issue updating the engineers information'
    return render_template('engineers.html', engineers_list=engineers_list)

@app.route('/delete/engineer/<int:engineer_id>', methods=['POST'])
def engineers_delete(engineer_id):
    eng = engineer.query.get_or_404(engineer_id)
    job_detail = jobs_detail.query.get_or_404(job_id)
    try:
        db.session.delete(eng)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        error_message = traceback.format_exc()
        log.debug(error_message + str(e))
        print(error_message + str(e))
        return 'There was an issue deleting the engineer information'
    return redirect('/engineers')

@app.route('/engineers/<int:engineer_id>/detail', methods=['GET', 'POST'])
def engineer_detail_view(engineer_id):
    eng = engineer.query.get_or_404(engineer_id)

    if request.method == 'POST':
        eng.engineer_name = request.form.get('engineer_name') or None
        eng.engineer_contact = request.form.get('engineer_contact') or None
        eng.engineer_phone = request.form.get('engineer_phone') or None
        try:
            db.session.commit()
            return redirect('/engineers')
        except Exception as e:
            db.session.rollback()
            error_message = traceback.format_exc()
            log.error(error_message + str(e))
            print(error_message + str(e))
            return 'There was an issue updating the engineer', 500
    # GET
    return render_template('engineers_detail.html', engineer=eng)

@app.route("/detail/<int:job_id>/edit_commission", methods=["GET", "POST"])
def job_commission_edit(job_id):
    """Edit job commission details."""
    job_detail = jobs_detail.query.get_or_404(job_id)
    jobs_summary = jobs_index.query.order_by(jobs_index.job_id).all()
    job_detail_totals = get_job_totals(job_id)

    parent_commission = jobs_commission.query.filter_by(job_id=job_id).first()
    if not parent_commission:
        return f"No commission record found for job {job_id}", 404

    eng = engineer_detail.query.filter_by(job_id=job_id).all()
    sales_details_for_job = sales_detail.query.filter_by(job_id=job_id).all()
    commission_lines = commission_detail_line.query.filter_by(job_id=job_id).all()

    if request.method == "POST":
        try:
            editable_fields = [
                "purchase_amount", "commission_at_sale", "commission_due_pct",
                "commission_adjust", "cause_of_adjustment", "commission_net_due",
                "notes", "final_commission", "final_due", "commission_due_1", "du1_date",
            ]
            for field in editable_fields:
                setattr(parent_commission, field, clean_value(request.form.get(field, getattr(parent_commission, field))))

            db.session.commit()
            return redirect(f"/detail/{job_id}")

        except Exception:
            db.session.rollback()
            log.exception(f"Error updating commission for job_id={job_id}")
            return "There was an issue updating the job commission", 500

    # GET request
    return render_template(
        "detail_edit_commission.html",
        job_detail=job_detail,
        job_detail_totals=job_detail_totals,
        jobs_summary=jobs_summary,
        eng=eng,
        engineers_list=engineer.query.all(),
        sales_details_for_job=sales_details_for_job,
        sales_list=sales.query.all(),
        parent_commission_id=parent_commission,
        commission_lines_for_job=commission_lines,
    )

@app.route("/detail/delete_commission/<int:commission_line_id>", methods=["POST"])
def job_commission_delete(commission_line_id):
    """Deletes the commission entry (by commission_line_id) from jobs_commission_line."""
    try:
        # delete from the actual table, not the view
        commission_line = jobs_commission_line.query.get_or_404(commission_line_id)

        # find related job_id via parent commission
        parent_commission = jobs_commission.query.filter_by(commission_id=commission_line.commission_id).first()
        job_id = parent_commission.job_id if parent_commission else None

        db.session.delete(commission_line)
        db.session.commit()

        if job_id:
            return redirect(f"/detail/{job_id}")
        else:
            return redirect("/")
    except Exception as e:
        db.session.rollback()
        log.exception("Error deleting job commission line")
        return f"There was an issue deleting the job commission line: {e}", 500


@app.route('/detail/<int:job_id>/edit_engineer', methods=['POST'])
def job_engineer_edit(job_id):
    print("POST received for job_id:", job_id)
    selected_engineer_name = request.form.get('engineer_name')
    selected_engineer = engineer.query.filter_by(engineer_name=selected_engineer_name).first()
    if not selected_engineer:
        return 'Engineer not found', 400

    # Check if this job-engineer pair already exists to avoid duplicates
    existing_job_engineer = job_engineer.query.filter_by(job_id=job_id, engineer_id=selected_engineer.engineer_id).first()
    if not existing_job_engineer:
        new_job_engineer_assoc = job_engineer(job_id=job_id, engineer_id=selected_engineer.engineer_id)
        db.session.add(new_job_engineer_assoc)
        try:
            db.session.commit()
            return redirect(f'/detail/{job_id}')
        except Exception as e:
            db.session.rollback()
            error_message = traceback.format_exc()
            log.debug(error_message + str(e))
            print(error_message + str(e))
            return 'There was an issue updating the job engineer'
    else:
        # Already exists, just redirect
        return redirect(f'/detail/{job_id}')

@app.route('/detail/<int:job_id>/edit_sales', methods=['POST'])
def job_sales_edit(job_id):
    print("POST received for sales_id:")
    selected_sales_name = request.form.get('sales_name')
    job_percentage = request.form.get('job_percentage') or 100
    if job_percentage:
        try:
            float(job_percentage)
        except ValueError:
            return "Invalid job percentage. Must be numeric.", 400
        selected_sales = sales.query.filter_by(sales_name=selected_sales_name).first()
        if not selected_sales:
            return 'Sales not found', 400

    # Check if this job-sales pair already exists to avoid duplicates
    existing_job_sales = jobs_sales.query.filter_by(job_id=job_id, sales_id=selected_sales.sales_id).first()
    if not existing_job_sales:
        new_job_sales_assoc = jobs_sales(job_id=job_id, sales_id=selected_sales.sales_id, job_percentage=job_percentage)
        db.session.add(new_job_sales_assoc)
        try:
            db.session.commit()
            return redirect(f'/detail/{job_id}')
        except Exception as e:
            db.session.rollback()
            error_message = traceback.format_exc()
            log.debug(error_message + str(e))
            print(error_message + str(e))
            return 'There was an issue updating the job sales'
    else:
        # Already exists, just redirect
        return redirect(f'/detail/{job_id}')

@app.route("/detail/delete_sales/<int:auto_id>", methods=["POST"])
def job_sales_delete(auto_id):
    """Deletes the sales entry (by auto_id) from jobs_sales."""
    try:
        sales_to_delete = jobs_sales.query.get_or_404(auto_id)
        job_id = sales_to_delete.job_id
        db.session.delete(sales_to_delete)
        db.session.commit()
        return redirect(f"/detail/{job_id}")
    except Exception as e:
        db.session.rollback()
        log.exception("Error deleting job sales")
        return f"There was an issue deleting the job sales: {e}", 500

@app.route("/detail/delete_engineer/<int:auto_id>", methods=["POST"])
def job_engineer_delete(auto_id):
    """Deletes the engineer entry (by auto_id) from jobs_engineer."""
    try:
        engineer_to_delete = job_engineer.query.get_or_404(auto_id)
        job_id = engineer_to_delete.job_id
        db.session.delete(engineer_to_delete)
        db.session.commit()
        return redirect(f"/detail/{job_id}")
    except Exception as e:
        db.session.rollback()
        log.exception("Error deleting job engineer")
        return f"There was an issue deleting the job engineer: {e}", 500

@app.route('/sales', methods=['GET', 'POST'])
def sales_team():
    sales_list = sales.query.all()
    if request.method == 'POST':
        sales_name = request.form.get('sales_name')
        sales_contact = request.form.get('sales_contact')
        sales_phone = request.form.get('sales_phone')
        new_sales_obj = sales(
            sales_name=sales_name,
            sales_contact=sales_contact,
            sales_phone=sales_phone
        )
        try:
            db.session.add(new_sales_obj)
            db.session.commit()
            return redirect('/sales')
        except Exception as e:
            db.session.rollback()
            error_message = traceback.format_exc()
            log.debug(error_message + str(e))
            print(error_message + str(e))
            return 'There was an issue updating the sales information'
    return render_template('sales_team.html', sales_list=sales_list)

@app.route('/sales/<int:sales_id>/detail', methods=['GET', 'POST'])
def sales_detail_view(sales_id):
    sales_member= sales.query.get_or_404(sales_id)
    if request.method == 'POST':
        sales_member.sales_name = request.form.get('sales_name') or None
        sales_member.sales_contact = request.form.get('sales_contact') or None
        sales_member.sales_phone = request.form.get('sales_phone') or None
        try:
            db.session.commit()
            return redirect('/sales')
        except Exception as e:
            db.session.rollback()
            error_message = traceback.format_exc()
            log.error(error_message + str(e))
            print(error_message + str(e))
            return 'There was an issue updating the sales information', 500
    # GET
    return render_template('sales_detail.html', sales=sales_member)

@app.route('/delete/sales/<int:sales_id>', methods=['POST'])
def sales_team_delete(sales_id):
    sales_to_delete = sales.query.get_or_404(sales_id)
    db.session.delete(sales_to_delete)
    db.session.commit()
    return redirect('/sales')


if __name__ == "__main__":
    # Read environment variables (for Docker or local)
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    port = int(os.getenv("PORT", 38291))
    host = os.getenv("FLASK_RUN_HOST", "0.0.0.0" if os.getenv("DOCKER_ENV") else "127.0.0.1")

    # Run Flask app
    app.run(debug=debug, host=host, port=port)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()
