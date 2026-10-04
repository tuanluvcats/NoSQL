package com.huit.hrmbackend.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import java.util.Date;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Document(collection = "employees")
public class Employee {
    @Id
    private String id;
    private String employeeId;
    private String fullName;
    private String gender;
    private Date dateOfBirth;
    private String email;
    private String phone;
    private Address address;
    private String departmentCode;
    private String position;
    private Double salary;
    private Date hireDate;
    private List<String> skills;
    private Boolean active;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class Address {
        private String street;
        private String district;
        private String city;
    }
}