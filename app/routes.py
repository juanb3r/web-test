from app import app, db, api
from flask import (
    render_template,
    url_for,
    redirect,
    request,
    json,
    Response,
    flash,
    session,
    jsonify
)
from app.models import User, Course, Enrollment
from app.forms import RegisterForm, LoginForm
from flask_restx import Resource


################################################################################
# Rutas de la API

@api.route('/api', '/api/')
class GetAndPostUsers(Resource):

    #GET
    def get(self):
        '''Devuelve todos los usuarios a través del método GET'''
        return jsonify(User.objects.all())

    #POST
    def post(self):
        ''' Recibe el método POST por medio de postman u otros apis managment'''

        # data contiene toda la información enviada por medio del post
        data = api.payload
        new_user = User(
            user_id=data['user_id'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email']
        )
        new_user.set_password(data['password'])
        new_user.save()
        return jsonify(User.objects(user_id = data['user_id']))

@api.route('/api/<id>')
class GetUpdateDeleteUserByID(Resource):

    #GET
    def get(self, id):
        return jsonify(User.objects(user_id = id))

    #PUT
    def put(self, id):
        data = api.payload
        # Se actualiza el usuario con el id especificado en la ruta put, se usa el ** porque es una variable de doble empaquetado
        User.objects(user_id = id).update(**data)
        return jsonify(User.objects(user_id = id))

    #DELETE
    def delete(self, id):
        # Se actualiza el usuario con el id especificado en la ruta put, se usa el ** porque es una variable de doble empaquetado
        User.objects(user_id = id).delete()
        return jsonify(User.objects.all())
################################################################################

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html", index=True)


@app.route("/courses")
@app.route("/courses/<int:course_year>")
def courses(course_year=2024):
    """Devuelve el listado de todos los cursos existentes"""
    courses_data = Course.objects.all()
    return render_template(
        "courses.html", course=True, course_year=course_year, courses_data=courses_data
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    """Registro de usuario"""

    # Si ha iniciado sesión lo regresa al inicio
    if session.get("username"):
        return redirect(url_for("index"))

    # form objeto que contiene el formulario creado en la clase RegisterForm
    form = RegisterForm()
    if form.validate_on_submit():
        # Se obtiene el número total de estudiantes y se agrega uno para tener registro de su id
        user_id = User.objects.count() + 1
        # Se obtienen los datos del formulario por medio del atributo data
        email = form.email.data.lower()
        password = form.password.data
        first_name = form.first_name.data.title()
        last_name = form.last_name.data.title()

        # Se crea el usuario y se le hace un hash a la clave, luego se guarda
        new_user = User(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        new_user.set_password(password)
        new_user.save()

        # la tarjeta flash es para enviar un mensaje y el success es un parametro usado para el elemento html y que cambie su color
        flash("Registro satisfactorio", "success")
        return redirect("/index")
    return render_template(
        "register.html", register=True, form=form, title="Nuevo registro de usuario"
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Inicio de sesión de los usuarios"""
    if session.get("username"):
        return redirect(url_for("index"))

    # Se crea el objeto form de la clase LoginForm
    form = LoginForm()
    # Se valida el envío del formulario por medio de su botón submit
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        # Se crea un objeto user que corresponda al correo agregado
        user = User.objects(email=email).first()
        # Se verifica clave y usuario, se usa el método de la clase user get_password para decodificar la clave y comprobar que corresponda
        if user and user.get_password(password):
            flash(f"{user.first_name} Has ingresado satisfactoriamente", "success")
            # Se crea el registro con la función session, se asignan valores a la lista. Esta lista sirve para comprobar que el usuario registrado sea el mismo.
            session["user_id"] = user.user_id
            session["username"] = user.first_name
            return redirect(url_for("index"))
        else:
            flash("Hubo un error en el inicio de sesión", "danger")
    return render_template(
        "login.html", form=form, title="Inicio de sesión", login=True
    )


@app.route("/logout")
def logout():
    """Ruta que permite la terminación de la sesión"""

    # Se puede usar de las dos formas, asignando False o por medio del método pop de la lista session.
    session["user_id"] = False
    session.pop("username", None)
    return redirect(url_for("index"))


@app.route("/css-test")
def css():
    """Ruta de prueba, solo para corroborar css"""
    return render_template("css.html")


@app.route("/enrollment", methods=["GET", "POST"])
def enrollment():
    """Ruta de registro a cursos, si no está iniciada la sesión, devuelve a registro"""
    if not session.get("username"):
        return redirect(url_for("register"))

    # Se obtienen los datos del formulario en la página course por medio del botón enroll
    course_id = request.form.get("course_id")
    title = request.form.get("title")
    # Obtiene el usuario por medio la lista session
    user_id = session.get("user_id")

    # Se comprueba el registro al curso, si está registrado regresa a página anterior, si no permite el registro.
    if course_id:
        if Enrollment.objects(user_id=user_id, course_id=course_id):
            flash(f"Lo siento, estás registrado en este curso { title }", "danger")
            return redirect(url_for("courses"))
        else:
            enrollment = Enrollment(user_id=user_id, course_id=course_id)
            enrollment.save()
            flash("Registro de curso satisfactorio", "success")

    # Regresa una lista de objetos creados mediante la función aggregate del motor de mongoDB, el contenido fue generado a través de un pipeline usando el mongo compass. Este pipeline tiene como objetivo traer toda la información de los cursos a los que se ha registrado el estudiante.
    courses = list(
        User.objects.aggregate(
            *[
                {
                    "$lookup": {
                        "from": "enrollment",
                        "localField": "user_id",
                        "foreignField": "user_id",
                        "as": "r1",
                    }
                },
                {
                    "$unwind": {
                        "path": "$r1",
                        "includeArrayIndex": "r1_id",
                        "preserveNullAndEmptyArrays": False,
                    }
                },
                {
                    "$lookup": {
                        "from": "course",
                        "localField": "r1.course_id",
                        "foreignField": "course_id",
                        "as": "r2",
                    }
                },
                {"$unwind": {"path": "$r2", "preserveNullAndEmptyArrays": False}},
                {"$match": {"user_id": user_id}},
                {"$sort": {"course_id": 1}},
            ]
        )
    )
    return render_template(
        "enrollment.html", enrollment=True, courses=courses, title="Enrollment"
    )


# Para get en el form, method = "GET"
# @app.route("/enrollment")
# def enrollment():
#         course_id = request.args.get('course_id')
#         title = request.args.get('title')
#         credit = request.args.get('credits')
#         return render_template("enrollment.html", course = True , data = {"id": course_id, "title" : title, "credit" : credit })


# @app.route("/api/")
# @app.route("/api/<int:index>")
# def api(index=None):
#     """Ruta de la api del proyecto"""
#     if index == None:
#         jdata = courses_data
#     else:
#         if index <= len(courses_data):
#             jdata = courses_data[index]
#         else:
#             jdata = {"course_id": "unknown", "info": "Index Out of Range"}
#     return Response(json.dumps(jdata), mimetype="application/json")


@app.route("/user")
def user():
    """ruta que muestra todos los usuarios registrados"""
    # User( user_id = 1, first_name = "Juan", last_name = "Bermudez", email = "juan@ber.com", password = "pass321").save()
    # User( user_id = 2, first_name = "Rox", last_name = "Bracho", email = "rox@ber.com", password = "ros123").save()
    users = User.objects.all()
    return render_template("users.html", users=users)
