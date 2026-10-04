use("hrm_mongodb");

const deptCount = db.departments.countDocuments();
const empCount = db.employees.countDocuments();
const projCount = db.projects.countDocuments();

print("Số phòng ban: " + deptCount + " (Kỳ vọng: 4)");
print("Số nhân viên: " + empCount + " (Kỳ vọng: 10)");
print("Số dự án: " + projCount + " (Kỳ vọng: 4)");