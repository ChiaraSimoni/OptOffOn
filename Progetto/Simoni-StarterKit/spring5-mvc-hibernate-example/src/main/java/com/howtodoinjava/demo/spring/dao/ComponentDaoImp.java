package com.howtodoinjava.demo.spring.dao;

import com.howtodoinjava.demo.spring.model.Component;
import org.hibernate.FlushMode;
import org.hibernate.Session;
import org.hibernate.SessionFactory;
import org.hibernate.query.Query;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public class ComponentDaoImp implements ComponentDao{

    @Autowired
    private SessionFactory sessionFactory;

    @Override
    public void init() {
        sessionFactory.getCurrentSession().setHibernateFlushMode(FlushMode.ALWAYS);
    }
    @Override
    public void save(Component component) {
        sessionFactory.getCurrentSession().save(component);
    }

    @Override
    public void delete(Component component) {
        sessionFactory.getCurrentSession().delete(component);
    }

//   @Override
//   public void edit(Component component) {       sessionFactory.getCurrentSession().edit(component);    }

    @Override
    public List<Component> list() {
        @SuppressWarnings("unchecked")
        Session session = sessionFactory.openSession();

        for(String key : session.getProperties().keySet() ){
            System.out.println("[DEBUG] key: " + key + " - property : " + session.getProperties().get(key));
        }
        System.out.println(session.getProperties());

        Query q = session.createQuery("From Component");

        List<Component> resultList = q.list();
        System.out.println("[DEBUG] num of components:" + resultList.size());
        for (Component next : resultList) {
            System.out.println("[DEBUG] next component: " + next);
        }

        return q.getResultList();
    }

}
