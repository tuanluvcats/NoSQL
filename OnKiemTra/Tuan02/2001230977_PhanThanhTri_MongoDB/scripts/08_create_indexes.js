use("hrm_mongodb");

// 1. Tạo unique index cho departmentCode trên collection departments
db.departments.createIndex({ departmentCode: 1 }, { unique: true });

// 2. Tạo unique index cho employeeId trên collection employees
db.employees.createIndex({ employeeId: 1 }, { unique: true });

// 3. Tạo unique index cho email trên collection employees
db.employees.createIndex({ email: 1 }, { unique: true });

// 4. Tạo unique index cho projectId trên collection projects
db.projects.createIndex({ projectId: 1 }, { unique: true });

// 5. Tạo compound index cho departmentCode và salary trên collection employees
db.employees.createIndex({ departmentCode: 1, salary: 1 });

// 6. Hiển thị danh sách index của collection employees
db.employees.getIndexes();