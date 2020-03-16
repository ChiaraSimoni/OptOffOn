package com.howtodoinjava.demo.spring.service;

import com.howtodoinjava.demo.spring.dao.ComponentDao;
import com.howtodoinjava.demo.spring.model.Component;
import com.howtodoinjava.demo.spring.model.Component;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class ComponentServiceImp implements ComponentService{

    @Autowired
    private ComponentDao componentDao;

    @Transactional
    public void init() {
        componentDao.init();
    }

    @Transactional
    public void save(Component component) {
        componentDao.save(component);
    }

    @Transactional
    public void delete(Long id) {

        for(Component c : list()){
            if (c.getId().equals(id)){
                componentDao.delete(c);
            }
        }

    }

    @Transactional(readOnly = true)
    public List<Component> list() {
        return componentDao.list();
    }
}
