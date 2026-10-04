use("hrm_mongodb");

// 1 & 2. Chỉ hiển thị mã, họ tên, lương và KHÔNG hiển thị _id
db.employees.find(
    {}, 
    { employeeId: 1, fullName: 1, salary: 1, _id: 0 }
);

// 3. Hiển thị tên, phòng ban và kỹ năng của nhân viên đang làm việc
db.employees.find(
    { active: true }, 
    { fullName: 1, departmentCode: 1, skills: 1, _id: 0 }
);

// 4. Sắp xếp nhân viên theo lương tăng dần (1 là tăng dần)
db.employees.find().sort({ salary: 1 });

// 5. Sắp xếp nhân viên theo lương giảm dần (-1 là giảm dần)
db.employees.find().sort({ salary: -1 });

// 6. Hiển thị ba nhân viên có lương cao nhất
db.employees.find().sort({ salary: -1 }).limit(3);

// 7. Bỏ qua ba nhân viên đầu và lấy ba nhân viên tiếp theo
db.employees.find().sort({ salary: -1 }).skip(3).limit(3);

// 8. Sắp xếp theo phòng ban (tăng dần), sau đó theo lương giảm dần
db.employees.find().sort({ departmentCode: 1, salary: -1 });