from backend.config import db
from flask_login import login_user, logout_user, login_required, current_user
from flask import Blueprint, render_template, redirect, url_for, flash

# Absolute imports
from backend.users.models import User
from backend.users.forms import LoginForm, RegistrationForm

users_blueprint = Blueprint('users', __name__)

@users_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    # Se o usuário já está logado, redirecione para o core
    if current_user.is_authenticated:
        return redirect(url_for('core.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.check_password(form.password.data):
            login_user(user)
            flash('Login efetuado com sucesso')
            return redirect(url_for('core.index'))
        else:
            flash('Login incorreto. Tente novamente')

    return render_template('core/login.html', form=form)

@users_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    # Se o usuário já está logado, redirecione para o core
    if current_user.is_authenticated:   
        return redirect(url_for('core.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)

        db.session.add(user)
        db.session.commit()
        flash('Obrigado, recebemos o seu cadastro!')

        return redirect(url_for('users.login'))

    return render_template('core/register.html', form=form)

@users_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout efetuado com sucesso')
    return redirect(url_for('users.login'))

@users_blueprint.route('/profile')
@login_required
def profile():
    # Exibir informações do perfil do usuário logado
    return render_template('profile.html', user=current_user)