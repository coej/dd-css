from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask.ext.login import login_required, current_user
from flask.ext.sqlalchemy import get_debug_queries
from . import main
from .forms import EditProfileForm
from .. import db
from ..models import User
from ..util import load_from_mongo
from ..util import get_file_params
from ..util import remove_from_mongo
from bson.objectid import ObjectId

@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['DD_CSS_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response


@main.route('/docs')
def about():
    return redirect('docs/')

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'

"""
@main.route('/user/<username>/<id>')
def download(id,username):
    queries = load_from_mongo("ddcss","queries", criteria={"id" : id}, projection = {"username": 0} )
    return queries # as a response
"""

def is_accessible(username):
    return current_user.username == username or current_user.get_id() == u'1'

@main.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    queries = None
    if is_accessible(username):
        queries = load_from_mongo("ddcss","queries", criteria={"username" : username}, projection = {"data": 0}, sorting = ("created_time", -1) )
    return render_template('user.html', user=user, queries=queries)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/query/<file_id>')
@login_required
def download(file_id):
    fformat = request.args.get('fformat')
    (file_basename, server_path, file_size) = get_file_params(file_id, fformat)
    response = make_response()
    response.headers['Content-Description'] = 'File Transfer'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers['Content-Disposition'] = 'attachment; filename=%s' % file_basename
    response.headers['Content-Length'] = file_size
    response.headers['X-Accel-Redirect'] = server_path # nginx: http://wiki.nginx.org/NginxXSendfile
    return response

@main.route('/remove/<file_id>')
@login_required
def remove(file_id):
    remove_from_mongo("ddcss","queries", criteria={"_id" : ObjectId(file_id)})
    flash('Your query has been removed.')
    return redirect(url_for('.user', username=current_user.username))

