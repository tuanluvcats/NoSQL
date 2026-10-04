use("hrm_mongodb");

// 1. Tìm nhân viên sống tại TP.HCM
db.employees.find({ "address.city": "TP.HCM" });

// 2. Tìm nhân viên sống tại Quận 1
db.employees.find({ "address.district": "Quận 1" });

// 3. Tìm nhân viên có kỹ năng Java
db.employees.find({ skills: "Java" });

// 4. Tìm nhân viên có đồng thời Java và MongoDB
db.employees.find({ 
    skills: { $all: ["Java", "MongoDB"] } 
});

// 5. Tìm nhân viên có một trong hai kỹ năng Redis hoặc Docker
db.employees.find({ 
    skills: { $in: ["Redis", "Docker"] } 
});

// 6. Tìm nhân viên phòng IT có kỹ năng Docker
db.employees.find({ 
    departmentCode: "IT", 
    skills: "Docker" 
});

// 7. Tìm dự án có nhân viên E001 tham gia
db.projects.find({ "members.employeeId": "E001" });

// 8. Tìm dự án có thành viên làm trên 20 giờ mỗi tuần
db.projects.find({ "members.hoursPerWeek": { $gt: 20 } });

// 9. Tìm dự án có E008 làm Frontend Developer
db.projects.find({
    members: { 
        $elemMatch: { 
            employeeId: "E008", 
            role: "Frontend Developer" 
        } 
    }
});