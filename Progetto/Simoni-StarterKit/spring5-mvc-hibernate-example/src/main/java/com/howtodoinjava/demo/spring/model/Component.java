package com.howtodoinjava.demo.spring.model;

import org.hibernate.validator.constraints.NotEmpty;

import javax.persistence.*;
import javax.validation.constraints.Size;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;

/*
@Entity
@Table
public class Component {
    @Id
    @GeneratedValue
    private Long id;

    private String name;

    private Boolean active;
*/
@Entity
@Table(name = "COMPONENTS")
public class Component implements Serializable {

    @Id
    @GeneratedValue
    @Column(name = "COMPONENT_ID")
    private Long id;

    @Column(name = "COMPONENT_COLUMN")
    private Long column;

    @Column(name = "COMPONENT_ELEMENTS_LIST")
    private ArrayList<String> list;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getColumn() {
        return id;
    }

    public void setColumn(Long column) {
        this.column = id;
    }

    public ArrayList<String> getList() {
        return list;
    }

    public void setList(ArrayList<String> list) {
        this.list = list;
    }

}