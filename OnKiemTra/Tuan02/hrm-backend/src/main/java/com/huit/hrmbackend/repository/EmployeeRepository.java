package com.huit.hrmbackend.repository;
import com.huit.hrmbackend.model.DepartmentStats;
import org.springframework.data.mongodb.repository.Aggregation;
import com.huit.hrmbackend.model.Employee;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface EmployeeRepository extends MongoRepository<Employee, String> {
    @Aggregation(pipeline = {
            "{ $group: { _id: '$departmentCode', soNhanVien: { $sum: 1 }, luongTrungBinh: { $avg: '$salary' } } }"
    })
    List<DepartmentStats> getDepartmentStats();
    // Tìm kiếm chính xác theo mã nhân viên
    Optional<Employee> findByEmployeeId(String employeeId);

    // Tìm kiếm tương đối theo tên
    List<Employee> findByFullNameContainingIgnoreCase(String fullName);

    // Lọc theo phòng ban[cite: 4]
    List<Employee> findByDepartmentCode(String departmentCode);

    // Lọc theo trạng thái làm việc
    List<Employee> findByActive(Boolean active);

    // Lọc nhân viên theo khoảng lương
    List<Employee> findBySalaryBetween(Double minSalary, Double maxSalary);
}