package com.howtodoinjava.demo.spring.service;

import java.util.List;

import com.howtodoinjava.demo.spring.model.User;

public interface UserService {
   void save(User user);
   void delete(String user);
//   void edit(User user);
   List<User> list();
}
