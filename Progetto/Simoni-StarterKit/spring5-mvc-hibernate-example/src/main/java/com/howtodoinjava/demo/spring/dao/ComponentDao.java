package com.howtodoinjava.demo.spring.dao;

import com.howtodoinjava.demo.spring.model.Component;

import java.util.List;

public interface ComponentDao {
    void init();
    void save(Component component);
    void delete(Component component);
    //void edit(Component component);
    List<Component> list();
}


