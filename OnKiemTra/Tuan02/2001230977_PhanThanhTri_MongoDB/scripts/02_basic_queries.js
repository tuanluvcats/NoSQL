use("hrm_mongodb");

// 1. Hiển thị toàn bộ nhân viên
db.employees.find();

// 2. Tìm nhân viên có mã E005
db.employees.findOne({ employeeId: "E005" });

// 3. Tìm nhân viên đang làm việc (active = true)
db.employees.find({ active: true });

// 4. Tìm nhân viên thuộc phòng IT
db.employees.find({ departmentCode: "IT" });

// 5. Tìm nhân viên có lương trên 20 triệu
db.employees.find({ salary: { $gt: 20000000 } });

// 6. Tìm nhân viên có lương từ 15 đến 25 triệu
db.employees.find({ 
    salary: { $gte: 15000000, $lte: 25000000 } 
});

// 7. Tìm nhân viên phòng IT đang làm việc
db.employees.find({ 
    departmentCode: "IT", 
    active: true 
});

// 8. Tìm nhân viên không thuộc phòng HR
db.employees.find({ departmentCode: { $ne: "HR" } });