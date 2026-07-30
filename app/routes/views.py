from flask import Blueprint, render_template

views_bp = Blueprint('views', __name__)

@views_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@views_bp.route('/login', methods=['GET'])
def login_view():
    return render_template('auth.html')

@views_bp.route('/register', methods=['GET'])
def register_view():
    return render_template('auth.html')

@views_bp.route('/events', methods=['GET'])
def list_events_view():
    return render_template('events.html')

@views_bp.route('/events/<int:id>', methods=['GET'])
def event_detail_view(id: int):
    return render_template('event_detail.html', event_id=id)

@views_bp.route('/dashboard', methods=['GET'])
def volunteer_dashboard_view():
    return render_template('dashboard.html')

@views_bp.route('/organization/dashboard', methods=['GET'])
def organization_dashboard_view():
    return render_template('organization_dashboard.html')

@views_bp.route('/organization/events/new', methods=['GET'])
def organization_event_new_view():
    return render_template('organization_event_new.html')

@views_bp.route('/organizations/<int:id>', methods=['GET'])
def organization_profile_view(id: int):
    return render_template('organization_profile.html', org_id=id)

@views_bp.route('/organizations', methods=['GET'])
def organizations_list_view():
    return render_template('organizations.html')

@views_bp.route('/quiz', methods=['GET'])
def quiz_view():
    return render_template('personality_test.html')
