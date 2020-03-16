<%--
  Created by IntelliJ IDEA.
  User: chiara
  Date: 1/19/20
  Time: 4:52 PM
  To change this template use File | Settings | File Templates.
--%>
<%@ page language="java" contentType="text/html; charset=ISO-8859-1"
         pageEncoding="ISO-8859-1"%>
<%@taglib prefix="form" uri="http://www.springframework.org/tags/form"%>
<%@taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core"%>
<%@taglib prefix="spring" uri="http://www.springframework.org/tags"%>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
<%--<style> <%@include file="/resources/core/css/hello.css"%></style>
<spring:url value="/resources/core/css/hello.css" var="coreCss" />
<spring:url value="/resources/core/css/bootstrap.min.css" var="bootstrapCss" />--%>

<!DOCTYPE html>
<html>
<head>
    <title>VPPs Management Dashboard</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-select@1.13.9/dist/css/bootstrap-select.min.css">
    <style> <%@include file="/resources/core/css/bootstrap.min.css"%></style>
    <style> <%@include file="/resources/core/css/hello.css"%></style>

    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/js/bootstrap.min.js"></script>

</head>
<body>
<div id="main body" class="container-fluid">
    <h1>VPPs Management Dashboard</h1>
    <div class="card card-body">
        <div id="podsconfig" class="container-fluid">
            <h2> 1 - Choose the PODs configuration:</h2>
            <%--CONFIG1--%>
            <div class="card card-body">
                <div id="form">
                    <form:form action="addComponent" method="post" modelAttribute="component">
                        <div class="row">
                            <div class="col-sm">
                                <h4> Components: </h4>
                                <form:select path="list" class="selectpicker" multiple="true" data-max-options="4">
                                    <form:option value="chp">Chp</form:option>
                                    <br>
                                    <form:option value="pv">Pv</form:option>
                                    <br>
                                    <form:option value="load">Load</form:option>
                                    <br>
                                    <form:option value="storage">Storage</form:option>
                                </form:select>
                            </div>
                            <div class="col-sm">
                                <h4> Replicate configuration? </h4>
                                Number of replicas: <input type="number" id="replicabox" name="num" value="1" min="1">
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-sm">
                                <br>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-sm">
                                <button type="submit" class="btn btn-primary">Add</button>
                            </div>
                        </div>
                    </form:form>
                </div>
                <div class="row">
                    <div class="col-sm">
                        <table class="table table-striped">
                            <thead>
                            <tr>
                                <th>ID</th>
                                <th>Components</th>
                            </tr>
                            </thead>

                            <c:forEach var="component" items="${components}" varStatus="status">
                                <tr>
                                    <td>${status.index}</td>
                                    <td>[
                                        <c:forEach var="items" items="${component.list}">
                                            ${items}_${status.index}
                                        </c:forEach>]
                                    </td>
                                    <td>
                                        <spring:url value="/components/${component.id}" var="componentUrl" />
                                        <spring:url value="/components/${component.id}/delete" var="deleteUrl" />

                                        <button class="btn btn-danger" type="button" onclick="this.disabled=true;location.href='${deleteUrl}'">Delete</button></td>
                                </tr>
                            </c:forEach>
                        </table>
                    </div>
                </div>
            </div>

        </div>
        <form action="execute" method="post">
            <div id="uncertainty" class="container-fluid">
                <h2> 2 - Choose where to apply uncertainty scenarios:</h2>
                <div class="card card-body">

                        <div class="custom-control custom-checkbox checkbox-xl">
                            <input type="checkbox" class="custom-control-input" id="uc1" name="uc1">
                            <label class="custom-control-label" for="uc1">Load</label>
                        </div>
                        <div class="custom-control custom-checkbox checkbox-xl">
                            <input type="checkbox" class="custom-control-input" id="uc2" name="uc2">
                            <label class="custom-control-label" for="uc2">PV</label>
                        </div>

                </div>

            </div>

            <div id="optimization" class="container-fluid">
                <h2> 3 - Choose the optimization steps:</h2>
                <div class="card card-body">

                        <div class="custom-control custom-checkbox checkbox-xl">
                            <input type="checkbox" class="custom-control-input" id="opt1" name="opt1">
                            <label class="custom-control-label" for="opt1">Offline</label>
                        </div>
                        <div class="custom-control custom-checkbox checkbox-xl">
                            <input type="checkbox" class="custom-control-input" id="opt2" name="opt2">
                            <label class="custom-control-label" for="opt2">Online</label>
                        </div>

                </div>
            </div>

            <div id="button" class="container-fluid">
                <br>
                <button type="submit" class="btn btn-dark"> Compute </button>
                <br>
            </div>
        </form>
    </div>
</div>

<script src="https://code.jquery.com/jquery-3.4.1.slim.min.js" integrity="sha384-J6qa4849blE2+poT4WnyKhv5vZF5SrPo0iEjwBvKU7imGFAV0wwj1yYfoRSJoZ+n" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.0/dist/umd/popper.min.js" integrity="sha384-Q6E9RHvbIyZFJoft+2mJbHaEWldlvI9IOYy5n3zV9zzTtmI3UksdQRVvoxMfooAo" crossorigin="anonymous"></script>
<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/js/bootstrap.min.js" integrity="sha384-wfSDF2E50Y2D1uUdj0O3uMBJnjuUD4Ih7YwaYd1iqfktj0Uod8GCExl3Og8ifwB6" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap-select@1.13.9/dist/js/bootstrap-select.min.js"></script>
</body>
</html>
