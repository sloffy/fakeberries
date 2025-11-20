from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    send_from_directory,
    abort,
)
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from decimal import Decimal, InvalidOperation
import os
from datetime import datetime
import bleach

from models import db, User, Product, create_default_admin


app = Flask(__name__)
app.config['SECRET_KEY'] = 'fakeberries-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fakeberries.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # 8MB для изображений

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
app.config['UPLOAD_FOLDER'] = os.path.join(INSTANCE_DIR, 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Инициализируем расширения
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Сначала войдите как admin.'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def save_image(file_storage):
    if not file_storage or not file_storage.filename:
        raise ValueError('Выберите изображение товара.')

    filename = secure_filename(file_storage.filename)
    if not allowed_file(filename):
        raise ValueError('Поддерживаются только изображения JPG, PNG, GIF или WEBP.')

    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
    name, ext = os.path.splitext(filename)
    final_filename = f"{timestamp}_{name[:40]}{ext.lower()}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], final_filename)

    file_storage.save(file_path)
    return final_filename


def parse_price(raw_price: str) -> Decimal:
    normalized = (raw_price or '').replace(',', '.').strip()
    if not normalized:
        raise ValueError('Укажите цену товара.')
    try:
        value = Decimal(normalized)
    except (InvalidOperation, ValueError):
        raise ValueError('Цена должна быть числом.')
    if value <= 0:
        raise ValueError('Цена должна быть больше нуля.')
    return value.quantize(Decimal('0.01'))


def get_redirect_target(default_endpoint: str = 'index') -> str:
    target = request.form.get('redirect') or request.args.get('next')
    if target and target.startswith('/'):
        return target.rstrip('?')
    return url_for(default_endpoint)


@app.route('/')
@login_required
def index():
    page = max(1, request.args.get('page', 1, type=int))
    per_page = 9
    pagination = Product.query.filter_by(status='catalog').order_by(
        Product.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'index.html',
        products=pagination.items,
        pagination=pagination,
        current_page=page,
    )


@app.route('/basket')
@login_required
def basket():
    basket_products = Product.query.filter_by(status='basket').order_by(Product.updated_at.desc()).all()
    total = sum((product.price_as_decimal() for product in basket_products), start=Decimal('0'))
    return render_template('basket.html', products=basket_products, total=total)


@app.route('/product/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = bleach.clean(request.form.get('name', '')).strip()
        price_raw = request.form.get('price', '')
        image = request.files.get('image')

        if not name:
            flash('Название товара обязательно.', 'error')
            return render_template('add_product.html', form_data=request.form)

        try:
            price_value = parse_price(price_raw)
            filename = save_image(image)
        except ValueError as exc:
            flash(str(exc), 'error')
            return render_template('add_product.html', form_data=request.form)

        product = Product(
            name=name,
            price=price_value,
            image_filename=filename,
            status='catalog',
        )
        db.session.add(product)
        db.session.commit()
        flash('Товар добавлен в каталог FakeBerries!', 'success')
        return redirect(url_for('index'))

    return render_template('add_product.html', form_data=None)


@app.route('/product/<int:product_id>/add-to-basket', methods=['POST'])
@login_required
def move_to_basket(product_id):
    product = Product.query.get_or_404(product_id)
    if product.status == 'basket':
        flash('Товар уже в корзине.', 'info')
        return redirect(get_redirect_target())

    product.status = 'basket'
    db.session.commit()
    flash(f'"{product.name}" перемещён в корзину.', 'success')
    return redirect(get_redirect_target())


@app.route('/product/<int:product_id>/return-to-catalog', methods=['POST'])
@login_required
def return_to_catalog(product_id):
    product = Product.query.get_or_404(product_id)
    if product.status == 'catalog':
        flash('Товар уже находится в каталоге.', 'info')
        return redirect(get_redirect_target('basket'))

    product.status = 'catalog'
    db.session.commit()
    flash(f'"{product.name}" снова доступен на главной странице.', 'success')
    return redirect(get_redirect_target('basket'))


@app.route('/product/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    product.delete_image()
    db.session.delete(product)
    db.session.commit()
    flash('Товар удалён из системы.', 'success')
    return redirect(get_redirect_target())


@app.route('/basket/checkout', methods=['POST'])
@login_required
def checkout():
    basket_products = Product.query.filter_by(status='basket').all()
    if not basket_products:
        flash('Корзина уже пустая.', 'info')
        return redirect(url_for('basket'))

    for product in basket_products:
        product.delete_image()
        db.session.delete(product)
    db.session.commit()
    flash('Покупка оформлена. Корзина очищена.', 'success')
    return redirect(url_for('basket'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=bool(request.form.get('remember')))
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))

        flash('Неверные учётные данные.', 'error')

    return render_template('auth/login.html')


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/media/<path:filename>')
def media_file(filename):
    upload_dir = current_app.config.get('UPLOAD_FOLDER')
    if not upload_dir:
        abort(404)
    return send_from_directory(upload_dir, filename)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_admin()
    app.run(debug=True)