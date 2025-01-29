import json
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Файли для зберігання даних
ALBUMS_FILE = 'albums.json'
USERS_FILE = 'users.json'
ID_FILE = 'id.json'  # Файл для зберігання останнього використаного ID


# Клас для керування унікальними ідентифікаторами
class IDManager:
    @staticmethod
    def load_id():
        """Завантажує останній використаний ідентифікатор з файлу."""
        try:
            with open(ID_FILE, 'r') as file:
                return json.load(file)['last_id']
        except (FileNotFoundError, json.JSONDecodeError):
            return 0  # Якщо файлу немає або дані пошкоджені, починаємо з 0

    @staticmethod
    def save_id(last_id):
        """Зберігає останній використаний ідентифікатор в файл."""
        with open(ID_FILE, 'w') as file:
            json.dump({"last_id": last_id}, file, indent=4)

    @staticmethod
    def get_next_id():
        """Отримує наступний унікальний ідентифікатор та оновлює останній використаний."""
        current_id = IDManager.load_id()
        next_id = current_id + 1
        IDManager.save_id(next_id)  # Оновлюємо останній використаний ID
        return next_id


# Клас для роботи з альбомами
class AlbumManager:
    @staticmethod
    def load_file(file_path, default_data=None):
        """Завантажує дані з JSON-файлу, якщо файл існує та не пошкоджений."""
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return default_data if default_data is not None else []

    @staticmethod
    def save_file(file_path, data):
        """Зберігає дані у JSON-файл."""
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

    @staticmethod
    def load_albums():
        return AlbumManager.load_file(ALBUMS_FILE, default_data=[])

    @staticmethod
    def save_albums(albums):
        AlbumManager.save_file(ALBUMS_FILE, albums)

    @staticmethod
    def get_album_by_id(album_id):
        albums = AlbumManager.load_albums()
        return next((album for album in albums if album['id'] == album_id), None)

    @staticmethod
    def delete_album(album_id):
        albums = AlbumManager.load_albums()
        albums = [album for album in albums if album['id'] != album_id]
        AlbumManager.save_albums(albums)

    @staticmethod
    def add_album(title, description, release_date):
        albums = AlbumManager.load_albums()
        new_album = {
            'id': IDManager.get_next_id(),  # Використовуємо IDManager для унікальних ID
            'title': title,
            'description': description,
            'release_date': release_date
        }
        albums.append(new_album)
        AlbumManager.save_albums(albums)


# Клас для роботи з користувачами
class UserManager:
    @staticmethod
    def load_file(file_path, default_data=None):
        """Завантажує дані з JSON-файлу, якщо файл існує та не пошкоджений."""
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return default_data if default_data is not None else []

    @staticmethod
    def save_file(file_path, data):
        """Зберігає дані у JSON-файл."""
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

    @staticmethod
    def load_users():
        return UserManager.load_file(USERS_FILE, default_data={"admin": {"password": "admin123", "role": "admin"}})

    @staticmethod
    def save_users(users):
        UserManager.save_file(USERS_FILE, users)

    @staticmethod
    def register_user(username, password):
        users = UserManager.load_users()
        if username in users:
            return False  # Користувач вже існує
        users[username] = {"password": password, "role": "user"}
        UserManager.save_users(users)
        return True

    @staticmethod
    def authenticate_user(username, password):
        users = UserManager.load_users()
        return username in users and users[username]['password'] == password


# Рендеримо головну сторінку
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/history')
def history():
    return render_template('history.html')


@app.route('/albums')
def albums():
    albums = AlbumManager.load_albums()
    return render_template('album.html', albums=albums)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if UserManager.register_user(username, password):
            flash('Реєстрація успішна!')
            return redirect(url_for('login'))
        else:
            flash('Користувач вже існує!')
            return redirect(url_for('register'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if UserManager.authenticate_user(username, password):
            session['username'] = username
            flash('Вхід успішний!')
            return redirect(url_for('index'))
        else:
            flash('Невірний логін або пароль!')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Ви вийшли з акаунту!')
    return redirect(url_for('index'))


@app.route('/edit_album/<int:album_id>', methods=['GET', 'POST'])
def edit_album(album_id):
    album = AlbumManager.get_album_by_id(album_id)
    if album is None:
        flash('Альбом не знайдено!')
        return redirect(url_for('albums'))

    if request.method == 'POST':
        album['title'] = request.form['title']
        album['description'] = request.form['description']
        album['release_date'] = request.form['release_date']
        albums = AlbumManager.load_albums()
        AlbumManager.save_albums(albums)
        flash('Альбом оновлено!')
        return redirect(url_for('albums'))

    return render_template('edit_album.html', album=album)


@app.route('/add_album', methods=['GET', 'POST'])
def add_album():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        release_date = request.form['release_date']
        AlbumManager.add_album(title, description, release_date)
        flash('Альбом додано!')
        return redirect(url_for('albums'))
    return render_template('add_album.html')


@app.route('/delete_album/<int:album_id>', methods=['POST'])
def delete_album(album_id):
    AlbumManager.delete_album(album_id)
    flash('Альбом видалено!')
    return redirect(url_for('albums'))


if __name__ == '__main__':
    app.run(debug=True, port=5001)
