use("hrm_mongodb");

// 1. Thêm một nhân viên thử nghiệm có mã TEST01
db.employees.insertOne({ 
    employeeId: "TEST01", 
    fullName: "Nhân viên Test", 
    active: true 
});
// Kiểm tra xem đã thêm thành công chưa
db.employees.find({ employeeId: "TEST01" });

// 2. Xóa nhân viên TEST01 bằng deleteOne
db.employees.deleteOne({ employeeId: "TEST01" });
// Kiểm tra lại để chắc chắn đã xóa
db.employees.find({ employeeId: "TEST01" });

// 3. Thêm một dự án thử nghiệm có mã TESTP01
db.projects.insertOne({ 
    projectId: "TESTP01", 
    projectName: "Dự án Test" 
});
// Kiểm tra dữ liệu vừa thêm
db.projects.find({ projectId: "TESTP01" });

// 4. Xóa dự án TESTP01 bằng deleteOne
db.projects.deleteOne({ projectId: "TESTP01" });
// Kiểm tra lại
db.projects.find({ projectId: "TESTP01" });

// 5 & 6. Xóa tất cả nhân viên có active = false và kiểm tra số lượng trước/sau khi xóa
const countBefore = db.employees.countDocuments();
const inactiveCount = db.employees.countDocuments({ active: false });
print("Tổng số nhân viên TRƯỚC khi xóa: " + countBefore);
print("Số nhân viên đã nghỉ việc (active = false) chuẩn bị xóa: " + inactiveCount);

// Chạy lệnh xóa nhiều document
db.employees.deleteMany({ active: false });

const countAfter = db.employees.countDocuments();
print("Tổng số nhân viên SAU khi xóa: " + countAfter);