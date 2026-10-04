use("hrm_mongodb");

// 1 -> 5. Thống kê nhân viên theo phòng ban (Đếm số lượng, lương TB, Max, Min)
db.employees.aggregate([
    {
        $group: {
            _id: "$departmentCode",
            soNhanVien: { $sum: 1 },
            luongTrungBinh: { $avg: "$salary" },
            luongCaoNhat: { $max: "$salary" },
            luongThapNhat: { $min: "$salary" }
        }
    },
    {
        $match: { soNhanVien: { $gte: 2 } }
    }
]);

// 6. Đếm số dự án theo trạng thái
db.projects.aggregate([
    {
        $group: {
            _id: "$status",
            soLuongDuAn: { $sum: 1 }
        }
    }
]);

// 7. Tính tổng ngân sách các dự án đang thực hiện 
db.projects.aggregate([
    {
        $match: { status: "In Progress" }
    },
    {
        $group: {
            _id: null,
            tongNganSach: { $sum: "$budget" }
        }
    }
]);

// 8. Tách mảng skills để đếm số nhân viên theo từng kỹ năng
db.employees.aggregate([
    { $unwind: "$skills" },
    {
        $group: {
            _id: "$skills",
            soNhanVien: { $sum: 1 }
        }
    },
    { 
        $sort: { soNhanVien: -1 } 
    }
]);

// 9. Tách mảng members để đếm số thành viên của từng dự án
db.projects.aggregate([
    { $unwind: "$members" },
    {
        $group: {
            _id: {
                projectId: "$projectId", 
                projectName: "$projectName"
            },
            soThanhVien: { $sum: 1 }
        }
    },
    {
        $project: {
            _id: 0,
            maDuAn: "$_id.projectId",
            tenDuAn: "$_id.projectName",
            soThanhVien: 1
        }
    }
]);