from flask import Flask, render_template, request, redirect, url_for, session, flash
import csv
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'broder_coffee_secret'

menu_file = "Menu.csv"
riwayat_file = "riwayat_transaksi.csv"
pengguna = {"admin": "admin123"}

def baca_menu():
    try:
        with open(menu_file, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            return [{"nama": row["nama"], "harga": int(row["harga"])} for row in reader]
    except FileNotFoundError:
        return []

def quick_sort(data, key, ascending=True):
    if len(data) <= 1:
        return data
    pivot = data[len(data) // 2][key]
    left = [x for x in data if (x[key] < pivot and ascending) or (x[key] > pivot and not ascending)]
    middle = [x for x in data if x[key] == pivot]
    right = [x for x in data if (x[key] > pivot and ascending) or (x[key] < pivot and not ascending)]
    return quick_sort(left, key, ascending) + middle + quick_sort(right, key, ascending)

def binary_search(data, key, target):
    left, right = 0, len(data) - 1
    target = target.strip().lower()
    while left <= right:
        mid = (left + right) // 2
        mid_value = str(data[mid][key]).strip().lower()
        if mid_value == target:
            return data[mid]
        elif mid_value < target:
            left = mid + 1
        else:
            right = mid - 1
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        if user in pengguna and pengguna[user] == pw:
            session['username'] = user
            return redirect(url_for('dashboardadmin'))
        else:
            flash("❌ Username atau password salah.")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/dashboardadmin')
def dashboardadmin():
    if session.get('username') != 'admin':
        return redirect(url_for('login'))
    return render_template('dashboardadmin.html')

@app.route('/menu')
def menu():
    data_menu = baca_menu()
    sort = request.args.get('sort')
    order = request.args.get('order', 'asc') == 'asc'
    search = request.args.get('search')

    if sort in ['nama', 'harga']:
        data_menu = quick_sort(data_menu, sort, ascending=order)
    if search:
        search = search.strip()
        data_menu = quick_sort(data_menu, 'nama', ascending=True)
        hasil = binary_search(data_menu, 'nama', search)
        data_menu = [hasil] if hasil else []

    page = int(request.args.get('page', 1))
    per_page = 10
    start = (page - 1) * per_page
    end = start + per_page
    paginated_menu = data_menu[start:end]

    total_pages = (len(data_menu) + per_page - 1) // per_page

    return render_template(
        'menu.html',
        menu=paginated_menu,
        page=page,
        total_pages=total_pages,
        sort=sort,
        order='asc' if order else 'desc',
        search=search
    )

def load_menu():
    data = []
    try:
        with open('Menu.csv', mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader, None)  # Lewati header id,nama,harga
            for row in reader:
                if len(row) < 3:
                    continue  # skip jika kolom kurang
                try:
                    data.append({
                        "id": int(row[0].strip()),
                        "nama": row[1].strip(),
                        "harga": int(row[2].strip())
                    })
                except ValueError:
                    continue
    except FileNotFoundError:
        pass
    return data

@app.route('/addmenu', methods=['GET', 'POST'])
def addmenu():
    if request.method == 'POST':
        nama = request.form['nama']
        harga = request.form['harga']
        with open('Menu.csv', mode='a', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([nama, harga])
        return redirect('/addmenu')
    return render_menu_page('addmenu.html')

@app.route('/updatemenu', methods=['GET', 'POST'])
def updatemenu():
    if request.method == 'POST':
        nama_lama = request.form['nama_lama']
        nama_baru = request.form['nama_baru']
        harga_baru = request.form['harga_baru']
        data = load_menu()
        updated = False
        for item in data:
            if item['nama'] == nama_lama:
                item['nama'] = nama_baru
                item['harga'] = int(harga_baru)
                updated = True
        if updated:
            with open('Menu.csv', mode='w', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                for item in data:
                    writer.writerow([item['nama'], item['harga']])
        return redirect('/updatemenu')
    return render_menu_page('updatemenu.html')

@app.route('/deletemenu', methods=['GET', 'POST'])
def deletemenu():
    if request.method == 'POST':
        nama_hapus = request.form['nama_hapus']
        data = [item for item in load_menu() if item['nama'] != nama_hapus]
        with open('Menu.csv', mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            for item in data:
                writer.writerow([item['nama'], item['harga']])
        return redirect('/deletemenu')
    return render_menu_page('deletemenu.html')

def render_menu_page(template_name):
    page = int(request.args.get('page', 1))
    per_page = 10
    menu = load_menu()
    total = len(menu)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    return render_template(template_name, 
                           menu=menu[start:end], 
                           page=page, 
                           total_pages=total_pages)

@app.route('/pesan', methods=['GET', 'POST'])
def pesan():
    data_menu = baca_menu()
    if request.method == 'POST':
        pesanan = []
        jumlah_item = int(request.form.get('jumlah_item', 0))
        for i in range(jumlah_item):
            nama = request.form.get(f'nama_{i}')
            harga = int(request.form.get(f'harga_{i}', 0))
            qty = request.form.get(f'qty_{i}')
            if qty and qty.isdigit() and int(qty) > 0:
                pesanan.append({
                    "nama": nama,
                    "harga": harga,
                    "jumlah": int(qty)
                })
        if pesanan:
            waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            total = sum(p['harga'] * p['jumlah'] for p in pesanan)
            riwayat = {"waktu": waktu, "pesanan": pesanan, "total": total}
            simpan_riwayat(riwayat)
            return render_template('struk.html', struk=riwayat)
        else:
            flash("❌ Tidak ada pesanan.")
    return render_template('pesan.html', menu=data_menu)

@app.route('/riwayat')
def riwayat():
    tanggal_filter = request.args.get('tanggal')
    data = []

    try:
        with open(riwayat_file, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                waktu = row[0]
                if tanggal_filter and not waktu.startswith(tanggal_filter):
                    continue

                items = []
                total = 0
                for item in row[1:]:
                    try:
                        nama_part = item.split('(')[0].strip()
                        qty_harga = item.split('(')[1].replace(')', '')
                        qty_str, harga_str = qty_harga.split('x')
                        qty = int(qty_str.strip())
                        harga = int(harga_str.strip())
                        subtotal = qty * harga
                        total += subtotal
                        items.append({
                            "nama": nama_part,
                            "qty": qty,
                            "harga": harga,
                            "subtotal": subtotal
                        })
                    except (IndexError, ValueError):
                        continue

                data.append({
                    "waktu": waktu,
                    "items": items,
                    "total": total
                })
    except FileNotFoundError:
        data = []
    return render_template("riwayat.html", riwayat=data, tanggal=tanggal_filter)

def simpan_riwayat(riwayat):
    with open(riwayat_file, mode="a", encoding="utf-8", newline='') as file:
        writer = csv.writer(file)
        writer.writerow([riwayat['waktu']] + [f"{item['nama']} ({item['jumlah']} x {item['harga']})" for item in riwayat['pesanan']])

@app.route('/logout')
def logout():
    session.clear()
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
