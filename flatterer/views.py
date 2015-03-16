from random import shuffle
from functools import wraps

from flatterer import db, app, login_manager
from forms import *
from models import User, Gender, Compliment, Theme, Complimentee

from flask import (Blueprint, request, render_template, flash,
                   g, session, redirect)
from flask.ext.login import (login_user, logout_user, current_user,
                             login_required)


def require_admin(f):
    """Require administrator permissions."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.admin:
            return f(*args, **kwargs)
        return no_perms('You are not an admin!')
    return decorated_function


def require_complimentee_perms(f):
    """Requires someone to have permission to edit a complimentee."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        complimentee = (Complimentee.query
                        .filter_by(url=kwargs['user_url'])
                        .first())
        if complimentee:
            if complimentee.owner != g.user.id:
                return no_perms('You can not edit a complimentee '
                                'you did not create!')
        else:
            return no_perms('The complimentee you are looking for '
                            'does not exist!')
        return f(*args, **kwargs)
    return decorated_function


@app.before_request
def before_request():
    """Do stuff before a request happens."""
    g.user = current_user
    if g.user is None:
        g.user = User("", "Guest", "")
    g.login_form = LoginForm()


@app.route("/")
def home():
    """Home page."""
    return render_template("home.html", login_form=g.login_form, user=g.user)


@app.route("/no_perms")
def no_perms(msg):
    """Standard message page.

    TODO: Fix name and where it's used.
    """
    return render_template("message.html", login_form=g.login_form,
                           user=g.user, msg=msg)


@app.route("/register", methods=['GET', 'POST'])
def register():
    """Register page."""
    form = Register()
    message = ""

    if request.method == "POST":
        if form.password.data != form.confirm_pass.data:
            message = "The passwords provided did not match!\n"
        elif User.query.filter_by(username=form.username.data).all():
            message = "This username is taken!"
        else:
            # Add user to db
            user = User(name=form.name.data, username=form.username.data,
                        password=form.password.data, admin=form.admin.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Registered and logged in successfully!")
            return render_template('home.html', user=g.user,
                                   login_form=g.login_form)

    return render_template('register.html', user=g.user,
                           login_form=g.login_form, form=form,
                           message=message)


# For Flask-Login
@login_manager.user_loader
def load_user(userid):
    return User.query.filter_by(id=userid).first()


# For Flask-Login
def get_user():
    # A user id is sent in, to check against the session
    # and based on the result of querying that id we
    # return a user (whether it be a sqlachemy obj or an
    # obj named guest

    if 'user_id' in session:
            return User.query.filter_by(id=session["user_id"]).first()
    return None


# TODO: Hash passwords
@app.route("/login", methods=['GET', 'POST'])
def login():
    """Handles logins."""
    form = LoginForm(request.form, csrf_enabled=False)

    if form.validate_on_submit():
        # login and validate the user...
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Logged in successfully.")
            print "User=" + user.name

    return redirect("/")


@app.route("/logout", methods=['POST'])
def logout():
    """Logs out a user."""
    logout_user()
    flash("Logged out successfully!")
    return redirect("/")


@app.route("/get_info", methods=["GET", "POST"])
def get_info():
    """Gets information on a user to ready them to compliment."""
    form = Get_Info()

    if not g.user.is_anonymous():
        form.name.data = g.user.name
    if request.method == "POST":
        return compliment_gender_name(name=form.name.data,
                                      gender=form.gender.data)
    else:
        return render_template("get_info.html", login_form=g.login_form,
                               form=form, user=g.user)


@app.route("/add_complimentee", methods=["GET", "POST"])
@login_required
def add_complimentee():
    """Add a complimentee."""
    form = AddComplimentee()

    msg = ""
    if request.method == "POST":
        exists = Complimentee.query.filter_by(url=form.url.data).first()
        if form.url.data and not exists:
            complimentee = Complimentee(form.name.data,
                                        form.url.data,
                                        owner=g.user.id,
                                        greeting=form.greeting.data)
            db.session.add(complimentee)
            db.session.commit()
            msg = form.name.data + " added successfully!"
            return redirect(form.url.data+'/add_theme')
        else:
            msg = "This url is already taken!"

    return render_template('add_complimentee.html', login_form=g.login_form,
                           form=form, user=g.user, msg=msg)


@app.route("/add_gender", methods=['GET', 'POST'])
@require_admin
def add_gender():
    """Add a gender to the database."""
    form = AddGender()

    if request.method == "POST":
        # Add district to db.
        gender = Gender(form.gender.data)
        db.session.add(gender)
        db.session.commit()
    return render_template('add_gender.html', login_form=g.login_form,
                           form=form, user=g.user)


@app.route("/add_compliment", methods=['GET', 'POST'])
def add_compliment():
    """Add a compliment."""
    form = AddCompliment()
    msg = ""

    if request.method == "POST":
        add_compliment(form)
        msg = "Compliment successfully added!"

    return render_template('add_compliment.html', login_form=g.login_form,
                           form=form, user=g.user, msg=msg)


@app.route("/<user_url>/add_compliment", methods=['GET', 'POST'])
@login_required
@require_complimentee_perms
def add_individual_compliment(user_url):
    """Add compliment for a given individual."""
    form = AddCompliment()
    msg = ""
    user = Complimentee.query.filter_by(url=user_url).first()
    if request.method == "POST":
        add_compliment(form, user_id=user.id)
        msg = "Compliment successfully added!"
    return render_template('add_compliment.html', name=user.name, url=user_url,
                           login_form=g.login_form, form=form,
                           user=g.user, msg=msg)


@app.route("/<user_url>/edit_theme/", methods=['GET', 'POST'])
@login_required
@require_complimentee_perms
def edit_theme(user_url):
    """Edit the theme for a given user."""
    form = AddTheme()
    user = Complimentee.query.filter_by(url=user_url).first()
    theme = Theme.query.filter_by(user_id=user.id).first()
    msg = ""
    if not theme:
        return redirect('/'+user_url+'/add_theme')

    if request.method == "POST":
        theme.theme_path = form.theme_path.data
        theme.song_path = form.song_path.data
        db.session.commit()
        msg = "Theme added successfully!"
        return redirect(user.url+'/add_compliment')

    theme = Theme.query.filter_by(user_id=user.id).first()
    form.theme_path.data = theme.theme_path
    form.song_path.data = theme.song_path

    return render_template('edit_theme.html', login_form=g.login_form,
                           form=form, user=g.user, name=user.name)


@app.route("/<user_url>/add_theme/", methods=['GET', 'POST'])
@login_required
@require_complimentee_perms
def add_theme(user_url):
    """Add a theme for a given user."""
    form = AddTheme()
    user = Complimentee.query.filter_by(url=user_url).first()

    if request.method == "POST":
        if form.theme_path.data or form.song_path.data:
            theme = Theme(user.id, form.theme_path.data, form.song_path.data)
            db.session.add(theme)
            db.session.commit()
        return redirect(user_url+'/add_compliment')

    return render_template('add_theme.html', login_form=g.login_form,
                           form=form, user=g.user, name=user.name)


@login_required
@app.route("/list_complimentees", methods=['GET', 'POST'])
def list_complimentees():
    """List complimentees for a given account."""

    complimentees = Complimentee.query.filter_by(owner=g.user.id).all()
    return render_template("list_complimentees.html", login_form=g.login_form,
                           user=g.user, complimentees=complimentees)


@app.route("/compliment/<gender>/<name>", methods=['GET', 'POST'])
def compliment_gender_name(gender, name):
    """Compliment someone based on their gender and name.

    TODO: Change this to use _or, instead of appending query results.
    """
    gender_compliments = (Compliment.query
                          .filter_by(gender=gender)
                          .filter_by(approved=True)
                          .all())
    any_compliments = (Compliment.query
                       .filter_by(gender="Any")
                       .filter_by(approved=True)
                       .all())

    compliments = gender_compliments + any_compliments

    shuffle(compliments)
    return render_template("compliment.html", login_form=g.login_form,
                           name=name, user=g.user, compliments=compliments)


@app.route("/control_panel", methods=['GET', 'POST'])
@require_admin
def compliment_control_panel():
    """Compliment control panel for all users and compliments."""
    msg = ""
    if request.method == "POST":
        remove_ids = request.form.getlist('remove')
        remove_compliments(remove_ids)
        msg = str(len(remove_ids))+" compliments removed successfully!\n"

        approved_ids = request.form.getlist('approve')
        approve_compliments(approved_ids)
        msg += str(len(approved_ids))+" compliments approved!"

    male_comps = Compliment.query.filter_by(gender="Male").all()
    female_comps = Compliment.query.filter_by(gender="Female").all()
    any_comps = Compliment.query.filter_by(gender="Any").all()
    personal_comps = Compliment.query.filter_by(gender=None).all()

    compliment_titles = ["Male Compliments", "Female Compliments",
                         "Any Gender Compliments", "Personal Compliments"]

    compliment_list = [male_comps, female_comps,  any_comps, personal_comps]
    compliment_info = zip(compliment_titles, compliment_list)

    unapproved_comps = Compliment.query.filter_by(approved=False).all()

    return render_template("control_panel.html", login_form=g.login_form,
                           user=g.user, compliment_info=compliment_info,
                           unapproved_comps=unapproved_comps, msg=msg)


@app.route("/compliment/<user_url>")
def compliment_individual(user_url):
    """Compliment a given user."""
    youtube = 0
    user = check_for_complimentee(user_url)
    if not user:
        return no_perms("The user you are trying to compliment "
                        "does not exist!")
    compliments = Compliment.query.filter_by(user_id=user.id).all()
    theme = Theme.query.filter_by(user_id=user.id).first()
    if theme:
        youtube = str(theme.song_path).count("youtube")
        theme.song_path = theme.song_path.replace("watch?v=", "embed/")
    if compliments:
        greeting = Complimentee.query.filter_by(id=user.id).first().greeting
        return render_template("compliment_individual.html", user=g.user,
                               login_form=g.login_form, youtube=youtube,
                               greeting=greeting, name=user.name, theme=theme,
                               compliments=compliments)
    else:
        return "The name you provided is not in the database!"


def add_compliment(form, user_id=None):
    """Adds a compliment for a given user_id."""
    if user_id:
        compliment = Compliment(compliment=form.compliment.data,
                                user_id=user_id, approved=True)
        print "Personal compliment added."

    else:
        approved = not g.user.is_anonymous() and g.user.admin
        compliment = Compliment(compliment=form.compliment.data,
                                gender=form.gender.data,
                                approved=approved)
        print "Gender specific compliment added." + str(approved)

    db.session.add(compliment)
    db.session.commit()


def remove_compliments(compliment_ids):
    """Batch removes compliments based on their ids."""
    removals = (db.session.query(Compliment)
                    .filter(Compliment.id.in_(compliment_ids)).all())
    for removal in removals:
        db.session.delete(removal)
    db.session.commit()


def approve_compliments(compliment_ids):
    """Batch approve compliments."""
    approvals = (db.session.query(Compliment)
                    .filter(Compliment.id.in_(compliment_ids)).all())
    for compliment in approvals:
        compliment.approved = True
    db.session.commit()


def check_for_complimentee(url):
    """Check to see if a complimentee exists."""
    return Complimentee.query.filter_by(url=url).first()
