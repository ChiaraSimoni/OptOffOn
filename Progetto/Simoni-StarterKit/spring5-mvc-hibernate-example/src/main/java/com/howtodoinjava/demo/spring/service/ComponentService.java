package com.howtodoinjava.demo.spring.service;

import com.howtodoinjava.demo.spring.model.Component;

import java.util.List;

public interface ComponentService {
    void init();
    void save(Component component);
    void delete(Long id);
    //void edit(Component component);
    List<Component> list();
}
