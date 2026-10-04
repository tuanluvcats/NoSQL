package com.huit.hrmbackend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class HrmBackendApplication {

	public static void main(String[] args) {
		System.setProperty("spring.data.mongodb.uri", "mongodb://localhost:27017/hrm_mongodb");

		SpringApplication.run(HrmBackendApplication.class, args);
	}
}