package com.huit.hrmbackend.controller;

import com.huit.hrmbackend.model.Employee;
import com.huit.hrmbackend.repository.EmployeeRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Sort;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/employees")
@CrossOrigin(origins = "*")
public class EmployeeController {

    @Autowired
    private EmployeeRepository repository;

    // 1. Hiển thị danh sách và sắp xếp lương tăng/giảm
    @GetMapping
    public List<Employee> getAllEmployees(@RequestParam(required = false) String sort) {
        if ("asc".equals(sort)) {
            return repository.findAll(Sort.by(Sort.Direction.ASC, "salary"));
        } else if ("desc".equals(sort)) {
            return repository.findAll(Sort.by(Sort.Direction.DESC, "salary"));
        }
        return repository.findAll();
    }

    // 2. Tìm kiếm theo mã nhân viên
    @GetMapping("/search")
    public Employee getByEmployeeId(@RequestParam String employeeId) {
        return repository.findByEmployeeId(employeeId).orElse(null);
    }

    // 3. Lọc theo trạng thái làm việc
    @GetMapping("/filter/active")
    public List<Employee> filterByActive(@RequestParam Boolean status) {
        return repository.findByActive(status);
    }

    // 4. Thêm nhân viên mới
    @PostMapping
    public Employee createEmployee(@RequestBody Employee employee) {
        return repository.save(employee);
    }

    // 5. Cập nhật thông tin
    @PutMapping("/{id}")
    public Employee updateEmployee(@PathVariable String id, @RequestBody Employee employeeDetails) {
        employeeDetails.setId(id);
        return repository.save(employeeDetails);
    }

    // 6. Xóa nhân viên
    @DeleteMapping("/{id}")
    public void deleteEmployee(@PathVariable String id) {
        repository.deleteById(id);
    }

}