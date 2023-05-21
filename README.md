# dockurr

dockurr adalah proyek yang ditujukan untuk project-based learning mata kuliah
Komputasi Awan (MII212610) kelas KOMA UGM periode 2022 Genap. dockurr didesain
sebagai suatu layanan Container-as-a-Service (CaaS) yang pada dasarnya
menggunakan Docker Engine.

[Lihat diagram konsep/arsitektur](https://www.draw.io/?lightbox=1&edit=_blank#Uhttps%3A%2F%2Fraw.githubusercontent.com%2Fp4kl0nc4t%2Fdockurr%2Fmain%2Fdocs%2Fcaas-diagram.drawio)

## Anggota Kelompok

1. Kadek Ninda Nandita Putri
2. Rachel Naragifta
3. Ronggo Tsani Musyafa
4. Faiz Unisa Jazadi

## Tech stack

1. Docker
2. Flask (Python)
3. Celery
4. RabbitMQ
5. Jinja2

## Development Setup (WIP)

dockurr memerlukan Python 3.11 (belum dicoba di versi lain)
dan RabbitMQ.

1. Install requirements

   ```sh
   pip install -r requirements.txt
   ```

   Opsional, install juga development requirements

   ```sh
   pip install -r requirements.txt -r dev-requirements.txt
   ```

   Note: pengelolaan dependensi dilakukan dengan menggunakan
   [pip-tools](https://pip-tools.readthedocs.io/en/latest/).

2. Atur konfigurasi pada `config.toml` (salin dari `config-dist.toml`).

3. (Opsional) Jalankan RabbitMQ via Docker (bisa diinstall juga)

   ```sh
   docker run -d -p 5672:5672 rabbitmq
   ```

4. Jalankan semua service dengan command `./run-dev`

## Lisensi

MIT License

<!-- vim: set ft=markdown sw=3 sts=3 ts=3 et: -->
