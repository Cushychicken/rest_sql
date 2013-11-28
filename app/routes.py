#!flask/bin/python
from flask import Flask, jsonify, abort, make_response, request, url_for
from flask.ext.httpauth import HTTPBasicAuth
from flask.ext.restful import Api, Resource, marshal, fields, reqparse
from flask.ext.sqlalchemy import SQLAlchemy
import arrow

###############
### Configs ###
###############

# Basic app config
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

# Datbase config
db = SQLAlchemy(app)

# API and Authentication config
api = Api(app)
auth = HTTPBasicAuth()

# Debug/example tasklist
tasks = [
    {
        'id': 1,
        'title': u'Buy groceries',
        'description': u'Milk, Cheese, Pizza, Fruit, Tylenol', 
        'create_time': arrow.now().format('YYYY-MM-DD HH:mm:ss ZZ'),
        'done': False
    },
    {
        'id': 2,
        'title': u'Learn Python',
        'description': u'Need to find a good Python tutorial on the web', 
        'create_time': arrow.now().format('YYYY-MM-DD HH:mm:ss ZZ'),
        'done': False
    }
]

# Task list prototype
task_fields = {
    'title': fields.String,
    'description': fields.String,
    'done': fields.Boolean,
    'create_time': fields.String,
    'uri': fields.Url('task')
}

#########################
#### Database models ####
#########################

class Task(db.Model):
    __tablename__ = 'tasks'
    uid = db.Column(db.Integer, primary_key=True)
    create_date = db.Column(db.String(30))
    description = db.Column(db.String(200))
    done = db.Column(db.Integer)
    title = db.Column(db.String(50))

    def __init__(self, create_date, description, done, title):
        self.create_date = create_date
        self.description = description
        self.done = done
        self.title = title

###########################
#### Helper functions #####
###########################

def make_public_task(task):
    """
    Fills in tasks in internal DB so that the URI is returned, not the 
    task ID no
    """
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_single_task', 
                                      task_id = task['id'], 
                                      _external=True)
        else:
            new_task[field] = task[field]
    return new_task

#############################
##### API Functionality #####
#############################

class TaskListAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title',
                                   type=str,
                                   required=True,
                                   help='No task title provided',
                                   location='json')
        self.reqparse.add_argument('description',
                                   type=str,
                                   default="",
                                   location='json')
        super(TaskListAPI, self).__init__()

    def get(self):
        task_ret = Task.query.all()
        #print task_ret.uid, task_ret.title, task_ret.description
        for t in task_ret:
            print t.title
            print t.description
            print t.uid
        if not task_ret:
            abort(404)
        else:
            return jsonify(json_list=task_ret)

    def post(self):
        args = self.reqparse.parse_args()
        task = {
            'uid': db.session.query(Task).count() + 1,
            'create_time': arrow.now().format('YYYY-MM-DD HH:mm:ss ZZ'),
            'title': args['title'],
            'description': args['description'],
            'done': 0 
        }
        newtask = Task(task['create_time'],task['description'],task['done'],task['title'])
        db.session.add(newtask)
        db.session.commit()
        return { 'task': marshal(task, task_fields) }, 201

class TaskAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, location='json')
        self.reqparse.add_argument('description', type=str, location='json')
        self.reqparse.add_argument('done', type=bool, location='json')
        super(TaskAPI, self).__init__()

    def get(self, id):
        print id
        task_ret = Task.query.all()
        print task_ret.uid, task_ret.title, task_ret.description
        if not task_ret:
            abort(404)
        else:
            return { 'task': marshal(task_ret, task_fields) }        

    def put(self, id):
        task = filter(lambda t: t['id'] == id, tasks)
        if len(task) == 0:
            abort(404)
        task = task[0]
        args = self.reqparse.parse_args()
        for k, v in args.iteritems():
            if v != None:
                task[k] = args.get(k, task[k])
        return { 'task': marshal(task, task_fields) }

    def delete(self, id):
        task = filter(lambda t: t['id'] == id, tasks)
        if len(task) == 0:
            abort(404)
        else:
            tasks.remove(task[0])
            return jsonify( {'result': True } )

api.add_resource(TaskListAPI, '/todo/api/v1.0/tasks', endpoint='tasks')
api.add_resource(TaskAPI, '/todo/api/v1.0/tasks/<int:id>', endpoint='task')

@app.route('/testdb')
def testdb():
    if db.session.query("1").from_statement("SELECT 1").all():
        fetch = Task.query.filter_by(uid=6).first()
        print db.session.query(Task).count()
        if fetch:
            return fetch.description + ' ' + fetch.title 
        else:
            return 'No DB.'
    else:
        return 'Something is broken.'

##############################
##### Auth functionality #####
##############################

@auth.get_password
def get_password(username):
    if username == 'miguel':
        return 'python'
    return None

@auth.error_handler
def unauthorized():
    return make_response(jsonify( { 'error': 'Unauthorized access' } ), 401)

if __name__ == '__main__':
    db.create_all()
    app.run(debug = True)

