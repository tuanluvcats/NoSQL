use("hrm_mongodb");

// 1. Đổi số điện thoại của E002
db.employees.find({ employeeId: "E002" }, { phone: 1 });
db.employees.updateOne(
    { employeeId: "E002" },
    { $set: { phone: "0988888888" } }
);
db.employees.find({ employeeId: "E002" }, { phone: 1 });

// 2. Tăng lương E001 thêm 2 triệu đồng 
db.employees.find({ employeeId: "E001" }, { salary: 1 });
db.employees.updateOne(
    { employeeId: "E001" },
    { $inc: { salary: 2000000 } }
);
db.employees.find({ employeeId: "E001" }, { salary: 1 });

// 3. Chuyển E004 sang phòng SALE
db.employees.find({ employeeId: "E004" }, { departmentCode: 1 });
db.employees.updateOne(
    { employeeId: "E004" },
    { $set: { departmentCode: "SALE" } }
);
db.employees.find({ employeeId: "E004" }, { departmentCode: 1 });

// 4. Đánh dấu E008 đã nghỉ việc
db.employees.find({ employeeId: "E008" }, { active: 1 });
db.employees.updateOne(
    { employeeId: "E008" },
    { $set: { active: false } }
);
db.employees.find({ employeeId: "E008" }, { active: 1 });

// 5. Tăng 5% lương cho tất cả nhân viên phòng IT 
db.employees.find({ departmentCode: "IT" }, { employeeId: 1, salary: 1 });
db.employees.updateMany(
    { departmentCode: "IT" },
    { $mul: { salary: 1.05 } }
);
db.employees.find({ departmentCode: "IT" }, { employeeId: 1, salary: 1 });

// 6. Thêm kỹ năng Git cho E001 
db.employees.find({ employeeId: "E001" }, { skills: 1 });
db.employees.updateOne(
    { employeeId: "E001" },
    { $addToSet: { skills: "Git" } }
);
db.employees.find({ employeeId: "E001" }, { skills: 1 });

// 7. Thêm Git cho tất cả nhân viên đang làm việc 
db.employees.find({ active: true }, { employeeId: 1, skills: 1 });
db.employees.updateMany(
    { active: true },
    { $addToSet: { skills: "Git" } }
);
db.employees.find({ active: true }, { employeeId: 1, skills: 1 });

// 8. Xóa kỹ năng Redis khỏi E003 
db.employees.find({ employeeId: "E003" }, { skills: 1 });
db.employees.updateOne(
    { employeeId: "E003" },
    { $pull: { skills: "Redis" } }
);
db.employees.find({ employeeId: "E003" }, { skills: 1 });

// 9. Thêm E005 vào dự án P002 với vai trò Technical Consultant
db.projects.find({ projectId: "P002" }, { members: 1 });
db.projects.updateOne(
    { projectId: "P002" },
    { $push: { 
        members: { 
            employeeId: "E005", 
            role: "Technical Consultant", 
            joinDate: new Date(), 
            hoursPerWeek: 10 
        } 
    }}
);
db.projects.find({ projectId: "P002" }, { members: 1 });

// 10. Thay đổi số giờ làm của E008 trong dự án P001 thành 25 giờ
db.projects.find({ projectId: "P001" }, { members: 1 });
db.projects.updateOne(
    { projectId: "P001", "members.employeeId": "E008" },
    { $set: { "members.$.hoursPerWeek": 25 } }
);
db.projects.find({ projectId: "P001" }, { members: 1 });

// 11. Xóa E004 khỏi danh sách thành viên dự án P003
db.projects.find({ projectId: "P003" }, { members: 1 });
db.projects.updateOne(
    { projectId: "P003" },
    { $pull: { members: { employeeId: "E004" } } }
);
db.projects.find({ projectId: "P003" }, { members: 1 });