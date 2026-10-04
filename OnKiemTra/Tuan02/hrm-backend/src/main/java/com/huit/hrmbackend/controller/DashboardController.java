package com.huit.hrmbackend.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Sort;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.aggregation.Aggregation;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/dashboard")
@CrossOrigin(origins = "*")
public class DashboardController {

    @Autowired
    private MongoTemplate mongoTemplate;

    // 1. Dashboard Tổng quan
    @GetMapping("/overview")
    public Map<String, Object> getOverview() {
        Map<String, Object> stats = new HashMap<>();
        stats.put("totalDepts", mongoTemplate.getCollection("departments").countDocuments());
        stats.put("totalEmps", mongoTemplate.getCollection("employees").countDocuments());
        stats.put("activeEmps", mongoTemplate.count(new Query(Criteria.where("active").is(true)), "employees"));
        stats.put("inactiveEmps", mongoTemplate.count(new Query(Criteria.where("active").is(false)), "employees"));
        stats.put("totalProjects", mongoTemplate.getCollection("projects").countDocuments());
        stats.put("inProgress", mongoTemplate.count(new Query(Criteria.where("status").is("In Progress")), "projects"));
        stats.put("completed", mongoTemplate.count(new Query(Criteria.where("status").is("Completed")), "projects"));

        Aggregation budgetAgg = Aggregation.newAggregation(
                Aggregation.match(Criteria.where("status").is("In Progress")),
                Aggregation.group().sum("budget").as("totalBudget")
        );
        Map budgetResult = mongoTemplate.aggregate(budgetAgg, "projects", Map.class).getUniqueMappedResult();
        stats.put("totalBudget", budgetResult != null ? budgetResult.get("totalBudget") : 0);
        return stats;
    }

    // 2. Thống kê Phòng ban (Aggregation)
    @GetMapping("/departments")
    public List<Map> getDepartmentStats() {
        Aggregation agg = Aggregation.newAggregation(
                Aggregation.group("departmentCode")
                        .count().as("soNhanVien")
                        .avg("salary").as("luongTrungBinh")
                        .max("salary").as("luongCaoNhat")
                        .min("salary").as("luongThapNhat")
        );
        return mongoTemplate.aggregate(agg, "employees", Map.class).getMappedResults();
    }

    // 3. Thống kê Kỹ năng (Unwind & Group)
    @GetMapping("/skills")
    public List<Map> getSkillStats() {
        Aggregation agg = Aggregation.newAggregation(
                Aggregation.unwind("skills"),
                Aggregation.group("skills").count().as("soNhanVien"),
                Aggregation.sort(Sort.Direction.DESC, "soNhanVien")
        );
        return mongoTemplate.aggregate(agg, "employees", Map.class).getMappedResults();
    }

    // 4. Quản lý Dự án
    @GetMapping("/projects")
    public List<Map> getAllProjects() {
        return mongoTemplate.findAll(Map.class, "projects");
    }

    // 5. API Tương tác: Lấy nhân viên theo mã phòng
    @GetMapping("/employees/dept/{deptCode}")
    public List<Map> getEmployeesByDept(@PathVariable String deptCode) {
        return mongoTemplate.find(new Query(Criteria.where("departmentCode").is(deptCode)), Map.class, "employees");
    }
}