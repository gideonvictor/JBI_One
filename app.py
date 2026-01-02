import os
import sys
import logging
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, or_

from config import (
    mysql_username,
    mysql_password,
    mysql_host,
    mysql_port,
    mysql_dbname,
)

# -----------------------------------------------------------------------------
# Flask + SQLAlchemy setup
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+mysqldb://{mysql_username}:{mysql_password}@"
    f"{mysql_host}:{mysql_port}/{mysql_dbname}"
)
db = SQLAlchemy(app)

# Logging
logging.basicConfig(
    format="%(levelname)s - %(name)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

FILTERABLE_FIELDS = ("project_name", "account", "jbi_number", "market", "contractor")

# -----------------------------------------------------------------------------
# Utility helpers
# -----------------------------------------------------------------------------
def clean_value(val):
    """Normalize empty values to None."""
    if val is None or val == "" or str(val).lower() == "none":
        return None
    return val


def _to_float(v):
    """Safely convert database strings or numbers to float."""
    try:
        if v is None:
            return 0.0
        if isinstance(v, (int, float)):
            return float(v)

        # Normalize text representation
        v_str = str(v).strip().replace(",", "").replace("$", "")
        if v_str == "" or v_str.lower() in ("none", "null", "nan"):
            return 0.0
        return float(v_str)
    except Exception:
        return 0.0


def _commit_session(error_message):
    """Attempt to commit the current session, rolling back on failure."""
    try:
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        log.exception(error_message)
        return False


def _get_filter_values(args, fields=FILTERABLE_FIELDS):
    """Extract and normalize filter values from request args."""
    return {field: (args.get(field, type=str) or "").strip() for field in fields}


def _apply_filters(query, model, filters):
    """Apply ilike filters to a SQLAlchemy query for the provided fields."""
    for field, value in filters.items():
        if value:
            query = query.filter(getattr(model, field).ilike(f"%{value}%"))
    return query


def _calculate_totals(rows, amount_getter):
    """Aggregate monetary totals across rows using the provided accessor."""
    totals = {"purchase_amount": 0.0, "commission_at_sale": 0.0, "commission_net_due": 0.0}
    for row in rows:
        amounts = amount_getter(row) or {}
        for key in totals:
            totals[key] += _to_float(amounts.get(key))
    return totals


def get_job_totals(job_id):
    """
    Fetch purchase and commission totals for a given job_id from jobs_index.
    Returns a dict with the same keys used by detail_tiles.html.
    """
    job_index_entry = jobs_index.query.filter_by(job_id=job_id).first()
    if not job_index_entry:
        return {k: 0.0 for k in ["purchase_amount", "commission_at_sale", "commission_net_due"]}
    return _calculate_totals(
        [job_index_entry],
        lambda job: {
            "purchase_amount": job.purchase_amount,
            "commission_at_sale": job.commission_at_sale,
            "commission_net_due": job.commission_net_due,
        },
    )


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
    
class judy_task_line(db.Model):
    task_id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer)
    flag_complete = db.Column(db.Integer)
    task = db.Column(db.String(200))
    date = db.Column(db.Date)

    def __repr__(self):
        return f"<JudyTaskLine {self.task_id}:{self.task_id}>"


def _get_all_engineers():
    return engineer.query.order_by(engineer.engineer_name).all()


def _get_all_sales():
    return sales.query.order_by(sales.sales_name).all()

@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        try:
            job_id = (db.session.query(func.max(jobs.job_id)).scalar() or 0) + 1
            db.session.add_all([jobs(job_id=job_id), jobs_commission(job_id=job_id)])
            if _commit_session(f"Error adding new job with job_id={job_id}"):
                return redirect(f"/detail/{job_id}/edit")
            return "There was an issue adding your task", 500
        except Exception as e:
            db.session.rollback()
            log.exception("Error adding new job")
            return f"There was an issue adding your task: {str(e)}", 500

    try:
        filters = _get_filter_values(request.args)
        jobs_summary = (
            _apply_filters(jobs_index.query, jobs_index, filters)
            .order_by(jobs_index.job_id.desc())
            .all()
        )
        job_detail_totals = _calculate_totals(
            jobs_summary,
            lambda job: {
                "purchase_amount": job.purchase_amount,
                "commission_at_sale": job.commission_at_sale,
                "commission_net_due": job.commission_net_due,
            },
        )
        return render_template(
            "index.html",
            jobs_summary=jobs_summary,
            job_detail_totals=job_detail_totals,
            filters=filters,
        )
    except Exception:
        log.exception("Error loading index page")
        return "Error loading index page"

@app.route("/detail/<int:job_id>/commission_line", methods=["POST"])
def commission_line(job_id):
    commission_line_amount = request.form.get("commission_amount")
    commission_line_date = request.form.get("date")
    parent_commission_id = jobs_commission.query.filter_by(job_id=job_id).first().commission_id
    new_commission = jobs_commission_line(
        commission_amount=_to_float(commission_line_amount),
        date_commission=commission_line_date,
        commission_id=parent_commission_id,
    )
    db.session.add(new_commission)
    if _commit_session(f"Error updating commission line for job_id={job_id}"):
        return redirect(f"/detail/{job_id}")
    return "There was an issue updating the commission line information", 500
    
@app.route("/detail/<int:job_id>", methods=["GET"])
def detail(job_id):
    """View job detail page (read-only)."""
    try:
        job_detail = jobs_detail.query.get_or_404(job_id)
        jobs_summary = jobs_index.query.filter_by(job_id=job_id).first()

        eng = engineer_detail.query.filter_by(job_id=job_id).all()
        sales_details_for_job = sales_detail.query.filter_by(job_id=job_id).all()
        parent_commission = jobs_commission.query.filter_by(job_id=job_id).first()
        commission_lines = commission_detail_line.query.filter_by(job_id=job_id).all()
        judy_tasks = judy_task_line.query.filter_by(job_id=job_id).all()

        job_detail_totals = _calculate_totals(
            [jobs_summary] if jobs_summary else [],
            lambda job: {
                "purchase_amount": job.purchase_amount,
                "commission_at_sale": job.commission_at_sale,
                "commission_net_due": job.commission_net_due,
            },
        )

        return render_template(
            "detail.html",
            job_detail=job_detail,
            job_detail_totals=job_detail_totals,
            jobs_summary=jobs_summary,
            eng=eng,
            sales_details_for_job=sales_details_for_job,
            engineers_list=_get_all_engineers(),
            sales_list=_get_all_sales(),
            parent_commission_id=parent_commission,
            commission_lines_for_job=commission_lines,
            judy_tasks_for_job=judy_tasks,
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
        # Update all editable fields
        editable_fields = [
            "project_name", "account", "reference_contact", "phone_number",
            "equipment_description", "jbi_number", "market", "status",
            "contractor", "order_date", "ship_date", "complete",
        ]
        for field in editable_fields:
            setattr(job_detail, field, clean_value(request.form.get(field, getattr(job_detail, field))))

        if _commit_session(f"Error updating job detail for job_id={job_id}"):
            return redirect(f"/detail/{job_id}")

        return "There was an issue updating the header", 500

    return render_template(
        "detail_edit_job.html",
        job_detail=job_detail,
        job_detail_totals=job_detail_totals,
        jobs_summary=jobs_summary,
        eng=eng,
        sales_details_for_job=sales_details_for_job,
        engineers_list=_get_all_engineers(),
        sales_list=_get_all_sales(),
        parent_commission_id=parent_commission,
        commission_lines_for_job=commission_lines,
        show_save=True, cancel_url=f"/detail/{job_id}", title=f"{job_detail.project_name} - Edit Job"
    )

@app.route("/detail/<int:job_id>/judy_edit", methods=["GET", "POST"])
def detail_edit_judy(job_id):
    """Edit Judy task information."""
    job_detail = jobs_detail.query.get_or_404(job_id)
    jobs_summary = jobs_index.query.order_by(jobs_index.job_id).all()
    job_detail_totals = get_job_totals(job_id)

    eng = engineer_detail.query.filter_by(job_id=job_id).all()
    parent_commission = jobs_commission.query.filter_by(job_id=job_id).first()
    sales_details_for_job = sales_detail.query.filter_by(job_id=job_id).all()
    commission_lines = commission_detail_line.query.filter_by(job_id=job_id).all()

    if request.method == "POST":
        editable_fields = ["judy_task"]
        for field in editable_fields:
            setattr(job_detail, field, clean_value(request.form.get(field, getattr(job_detail, field))))

        if _commit_session(f"Error updating Judy task for job_id={job_id}"):
            return redirect(f"/detail/{job_id}")

        return "There was an issue updating the header", 500

    # GET request: render edit page
    return render_template(
        "detail_edit_judy.html",
        job_detail=job_detail,
        job_detail_totals=job_detail_totals,
        jobs_summary=jobs_summary,
        eng=eng,
        sales_details_for_job=sales_details_for_job,
        engineers_list=_get_all_engineers(),
        sales_list=_get_all_sales(),
        parent_commission_id=parent_commission,
        commission_lines_for_job=commission_lines,
        show_save=True, cancel_url=f"/detail/{job_id}", title="Edit Judy Task"
    )

@app.route("/engineers", methods=["GET", "POST"])
def engineers():
    engineers_list = engineer.query.order_by(engineer.engineer_name).all()
    if request.method == "POST":
        engineer_name = request.form.get("engineer_name")
        engineer_contact = request.form.get("engineer_contact")
        engineer_phone = request.form.get("engineer_phone")
        new_engineer = engineer(
            engineer_name=engineer_name,
            engineer_contact=engineer_contact,
            engineer_phone=engineer_phone
        )
        db.session.add(new_engineer)
        if _commit_session("Error updating the engineers information"):
            return redirect("/engineers")
        return "There was an issue updating the engineers information", 500
    return render_template("engineers.html", engineers_list=engineers_list)

@app.route("/delete/engineer/<int:engineer_id>", methods=["POST"])
def engineers_delete(engineer_id):
    eng = engineer.query.get_or_404(engineer_id)
    db.session.delete(eng)
    if not _commit_session("Error deleting the engineer information"):
        return "There was an issue deleting the engineer information", 500
    return redirect("/engineers")

@app.route("/engineers/<int:engineer_id>/detail", methods=["GET", "POST"])
def engineer_detail_view(engineer_id):
    eng = engineer.query.get_or_404(engineer_id)
    if request.method == "POST":
        eng.engineer_name = clean_value(request.form.get("engineer_name") or None)
        eng.engineer_contact = clean_value(request.form.get("engineer_contact") or None)
        eng.engineer_phone = clean_value(request.form.get("engineer_phone") or None)
        if _commit_session(f"Error updating engineer {engineer_id}"):
            return redirect("/engineers")
        return "There was an issue updating the engineer information", 500

    filters = _get_filter_values(request.args)
    jobs_query = (
        db.session.query(jobs_index, job_engineer.engineer_id)
        .join(job_engineer, jobs_index.job_id == job_engineer.job_id)
        .filter(job_engineer.engineer_id == engineer_id)
    )
    jobs_query = _apply_filters(jobs_query, jobs_index, filters)
    jobs_summary = jobs_query.order_by(jobs_index.job_id.desc()).all()
    job_detail_totals = _calculate_totals(
        jobs_summary,
        lambda row: {
            "purchase_amount": row[0].purchase_amount,
            "commission_at_sale": row[0].commission_at_sale,
            "commission_net_due": row[0].commission_net_due,
        },
    )

    return render_template(
        "engineers_detail.html",
        engineer=eng,
        jobs_summary=jobs_summary,
        job_detail_totals=job_detail_totals,
        filters=filters,
        show_save=True,
        cancel_url="/engineers",
        title="Engineers Detail",
    )


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
        editable_fields = [
            "purchase_amount", "commission_at_sale", "commission_due_pct",
            "commission_adjust", "cause_of_adjustment", "commission_net_due",
            "notes", "final_commission", "final_due", "commission_due_1", "du1_date",
        ]
        for field in editable_fields:
            setattr(parent_commission, field, clean_value(request.form.get(field, getattr(parent_commission, field))))

        if _commit_session(f"Error updating commission for job_id={job_id}"):
            return redirect(f"/detail/{job_id}")

        return "There was an issue updating the job commission", 500

    # GET request
    return render_template(
        "detail_edit_commission.html",
        job_detail=job_detail,
        job_detail_totals=job_detail_totals,
        jobs_summary=jobs_summary,
        eng=eng,
        engineers_list=_get_all_engineers(),
        sales_details_for_job=sales_details_for_job,
        sales_list=_get_all_sales(),
        parent_commission_id=parent_commission,
        commission_lines_for_job=commission_lines,
        show_save=True, cancel_url=f"/detail/{job_id}", title="Edit Commission Details"
    )

@app.route("/detail/delete_commission/<int:commission_line_id>", methods=["POST"])
def job_commission_delete(commission_line_id):
    """Deletes the commission entry (by commission_line_id) from jobs_commission_line."""
    commission_line = jobs_commission_line.query.get_or_404(commission_line_id)

    parent_commission = jobs_commission.query.filter_by(commission_id=commission_line.commission_id).first()
    job_id = parent_commission.job_id if parent_commission else None

    db.session.delete(commission_line)
    if _commit_session("Error deleting job commission line"):
        return redirect(f"/detail/{job_id}") if job_id else redirect("/")
    return "There was an issue deleting the job commission line", 500


@app.route("/detail/<int:job_id>/edit_engineer", methods=["POST"])
def job_engineer_edit(job_id):
    selected_engineer_name = request.form.get("engineer_name")
    selected_engineer = engineer.query.filter_by(engineer_name=selected_engineer_name).first()
    if not selected_engineer:
        return "Engineer not found", 400

    # Check if this job-engineer pair already exists to avoid duplicates
    existing_job_engineer = job_engineer.query.filter_by(job_id=job_id, engineer_id=selected_engineer.engineer_id).first()
    if not existing_job_engineer:
        new_job_engineer_assoc = job_engineer(job_id=job_id, engineer_id=selected_engineer.engineer_id)
        db.session.add(new_job_engineer_assoc)
        if _commit_session("Error updating the job engineer"):
            return redirect(f"/detail/{job_id}")
        return "There was an issue updating the job engineer", 500
    # Already exists, just redirect
    return redirect(f"/detail/{job_id}")

@app.route("/detail/<int:job_id>/edit_sales", methods=["POST"])
def job_sales_edit(job_id):
    selected_sales_name = request.form.get("sales_name")
    job_percentage = request.form.get("job_percentage") or 100

    try:
        float(job_percentage)
    except ValueError:
        return "Invalid job percentage. Must be numeric.", 400

    selected_sales = sales.query.filter_by(sales_name=selected_sales_name).first()
    if not selected_sales:
        return "Sales not found", 400

    # Check if this job-sales pair already exists to avoid duplicates
    existing_job_sales = jobs_sales.query.filter_by(job_id=job_id, sales_id=selected_sales.sales_id).first()
    if not existing_job_sales:
        new_job_sales_assoc = jobs_sales(job_id=job_id, sales_id=selected_sales.sales_id, job_percentage=job_percentage)
        db.session.add(new_job_sales_assoc)
        if _commit_session("Error updating the job sales"):
            return redirect(f"/detail/{job_id}")
        return "There was an issue updating the job sales", 500
    # Already exists, just redirect
    return redirect(f"/detail/{job_id}")

@app.route("/detail/delete_sales/<int:auto_id>", methods=["POST"])
def job_sales_delete(auto_id):
    """Deletes the sales entry (by auto_id) from jobs_sales."""
    sales_to_delete = jobs_sales.query.get_or_404(auto_id)
    job_id = sales_to_delete.job_id
    db.session.delete(sales_to_delete)
    if _commit_session("Error deleting job sales"):
        return redirect(f"/detail/{job_id}")
    return "There was an issue deleting the job sales", 500

@app.route("/detail/delete_engineer/<int:auto_id>", methods=["POST"])
def job_engineer_delete(auto_id):
    """Deletes the engineer entry (by auto_id) from jobs_engineer."""
    engineer_to_delete = job_engineer.query.get_or_404(auto_id)
    job_id = engineer_to_delete.job_id
    db.session.delete(engineer_to_delete)
    if _commit_session("Error deleting job engineer"):
        return redirect(f"/detail/{job_id}")
    return "There was an issue deleting the job engineer", 500

@app.route("/sales", methods=["GET", "POST"])
def sales_team():
    sales_list = _get_all_sales()
    if request.method == "POST":
        sales_name = request.form.get("sales_name")
        sales_contact = request.form.get("sales_contact")
        sales_phone = request.form.get("sales_phone")
        new_sales_obj = sales(
            sales_name=sales_name,
            sales_contact=sales_contact,
            sales_phone=sales_phone
        )
        db.session.add(new_sales_obj)
        if _commit_session("Error updating the sales information"):
            return redirect("/sales")
        return "There was an issue updating the sales information", 500
    return render_template("sales_team.html", sales_list=sales_list)

@app.route("/sales/<int:sales_id>/detail", methods=["GET", "POST"])
def sales_detail_view(sales_id):
    sales_member = sales.query.get_or_404(sales_id)

    q = (
        db.session.query(jobs_index, jobs_sales.job_percentage)
        .join(jobs_sales, jobs_index.job_id == jobs_sales.job_id)
        .filter(jobs_sales.sales_id == sales_id)
    )

    filters = _get_filter_values(request.args)
    q = _apply_filters(q, jobs_index, filters)

    jobs_summary = q.order_by(jobs_index.job_id.desc()).all()

    job_detail_totals = _calculate_totals(
        jobs_summary,
        lambda row: {
            "purchase_amount": _to_float(row[0].purchase_amount) * (_to_float(row[1]) / 100.0),
            "commission_at_sale": _to_float(row[0].commission_at_sale) * (_to_float(row[1]) / 100.0),
            "commission_net_due": _to_float(row[0].commission_net_due) * (_to_float(row[1]) / 100.0),
        },
    )

    if request.method == "POST":
        sales_member.sales_name = clean_value(request.form.get("sales_name") or None)
        sales_member.sales_contact = clean_value(request.form.get("sales_contact") or None)
        sales_member.sales_phone = clean_value(request.form.get("sales_phone") or None)
        if _commit_session(f"Error updating sales information for sales_id={sales_id}"):
            return redirect("/sales")
        return "There was an issue updating the sales information", 500

    return render_template(
        "sales_detail.html",
        sales=sales_member,
        jobs_summary=jobs_summary,
        job_detail_totals=job_detail_totals,
        filters=filters,
        show_save=True, cancel_url="/sales", title="Sales Detail"
    )


@app.route("/delete/sales/<int:sales_id>", methods=["POST"])
def sales_team_delete(sales_id):
    sales_to_delete = sales.query.get_or_404(sales_id)
    db.session.delete(sales_to_delete)
    if _commit_session(f"Error deleting sales member {sales_id}"):
        return redirect("/sales")
    return "There was an issue deleting the sales information", 500

@app.route("/judy_full_tasks", methods=["POST", "GET"])
def judy_full_tasks():
    one_month_ago = datetime.utcnow().date() - timedelta(days=30)

    all_tasks = (
        db.session.query(judy_task_line, jobs_index.project_name)
        .outerjoin(jobs_index, jobs_index.job_id == judy_task_line.job_id)
        .filter(
            or_(
                judy_task_line.flag_complete == 0,
                judy_task_line.date >= one_month_ago
            )
        )
        .order_by(judy_task_line.flag_complete, judy_task_line.date)
        .all()
    )
    try:
        return render_template("judy_full_tasks.html", all_tasks=all_tasks)
    except Exception:
        log.exception("Error loading Judy Task page")
        return "Error loading Judy Task page"

@app.route("/detail/<int:job_id>/add_judy_task", methods=["POST"])
def job_judy_add(job_id):
    judy_task = request.form.get("judy_task")
    judy_task_date = request.form.get("date")
    new_judy_task = judy_task_line(
        job_id=job_id,
        task=judy_task,
        flag_complete=0,
        date=judy_task_date
    )

    db.session.add(new_judy_task)
    if _commit_session("Error adding Judy task"):
        return redirect(f"/detail/{job_id}")
    return "There was an issue adding the Judy task", 500
    
@app.route("/detail/<int:job_id>/toggle_judy_task/<int:task_id>", methods=["POST"])
def job_judy_toggle(job_id, task_id):
    """Toggle the completion status of a Judy task."""
    task = judy_task_line.query.get_or_404(task_id)

    # Flip 0 → 1 or 1 → 0
    task.flag_complete = 0 if task.flag_complete == 1 else 1

    if _commit_session("Error toggling Judy task completion"):

        # Redirect back to where user came from
        ref = request.referrer or ""
        if "/judy_full_tasks" in ref:
            return redirect(url_for("judy_full_tasks"))
        return redirect(f"/detail/{job_id}")

    return "There was an issue updating the Judy task", 500

@app.route("/delete/judy_task/<int:task_id>", methods=["POST"])
def job_judy_delete(task_id):
    task_to_delete = judy_task_line.query.get_or_404(task_id)
    job_id = task_to_delete.job_id
    db.session.delete(task_to_delete)
    if _commit_session("Error deleting Judy task"):
        return redirect(f"/detail/{job_id}")
    return "There was an issue deleting the Judy task", 500


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