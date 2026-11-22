"""Danh sách tài liệu tham khảo dùng chung cho Chương 5 và cho việc đồng bộ vào file Word chính."""

REFS = {
    'c_install': 'DbSchema, “Installation”, DbSchema Documentation. https://dbschema.com/documentation/installation.html',
    'c_cassandra': 'DbSchema, trang về Apache Cassandra. https://dbschema.com/databases/cassandra/',
    'c_diagram': 'DbSchema, “Diagram”, DbSchema Documentation. https://dbschema.com/documentation/diagram.html',
    'c_sdoc': 'DbSchema, “Schema Documentation”, DbSchema Documentation. https://dbschema.com/documentation/schema-documentation.html',
    'c_syncdb': 'DbSchema, “Synchronize Database”, DbSchema Documentation. https://dbschema.com/documentation/synchronize-database.html',
    'c_gen': 'DbSchema, “Random Data Generator”, DbSchema Documentation. https://dbschema.com/documentation/random-data-generator.html',
    'c_fk': 'DbSchema, “Foreign Keys”, DbSchema Documentation. https://dbschema.com/documentation/foreign-keys.html',
    'c_sync': 'DbSchema, “Schema Synchronization”, DbSchema Documentation. https://dbschema.com/documentation/schema-synchronization.html',
    'c_git': 'DbSchema, “Git”, DbSchema Documentation. https://dbschema.com/documentation/git.html',
    'c_nosqlm': 'NoSQL Manager for Cassandra, trang sản phẩm. https://www.nosqlmanager.com/cassandra/',
    'slide': 'Bộ môn Hệ thống thông tin, Trường Đại học Công Thương TP.HCM, “Cơ sở dữ liệu NoSQL – Chương 3. Cơ sở dữ liệu Cassandra”, slide bài giảng, lưu hành nội bộ.',
    'book': 'J. Carpenter và E. Hewitt, Cassandra: The Definitive Guide – Distributed Data at Web Scale, 3rd ed., O’Reilly Media, 2020.',
    'guide': 'Nguyễn Văn Lễ, Nguyễn Thị Định, Tài liệu hướng dẫn thực hành Cơ sở dữ liệu NoSQL, Trường Đại học Công Thương TP.HCM, 2025, lưu hành nội bộ (Chương 2: Hệ quản trị cơ sở dữ liệu Cassandra).',
    'docker': 'Docker Inc., “cassandra – Official Image”, Docker Hub. https://hub.docker.com/_/cassandra (truy cập ngày 04/10/2026).',
    'dbsdoc': 'DbSchema, “DbSchema Documentation”. https://dbschema.com/documentation/ (truy cập ngày 04/10/2026).',
    'dbsprice': 'DbSchema, “Pricing – Compare plans”. https://dbschema.com/pricing (truy cập ngày 04/10/2026).',
    'jdbc': 'Wise Coders, “cassandra-jdbc-driver”, GitHub. https://github.com/wise-coders/cassandra-jdbc-driver (truy cập ngày 04/10/2026).',
    'cqlsh': 'Apache Cassandra, “cqlsh: the CQL shell”, Apache Cassandra Documentation. https://cassandra.apache.org/doc/latest/cassandra/managing/tools/cqlsh.html (truy cập ngày 04/10/2026).',
}

# Nguồn đã có trong Chương 1–4 của file Word chính, đánh [1]–[10] theo thứ tự "Nguồn tham khảo"
PRE_ORDER = ['c_install', 'c_cassandra', 'c_diagram', 'c_sdoc', 'c_syncdb', 'c_gen', 'c_fk', 'c_sync', 'c_git', 'c_nosqlm']
