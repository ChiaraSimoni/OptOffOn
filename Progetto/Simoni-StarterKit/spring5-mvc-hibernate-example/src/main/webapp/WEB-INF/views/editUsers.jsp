<%@ page language="java" contentType="text/html; charset=ISO-8859-1"
	pageEncoding="ISO-8859-1"%>
<%@taglib prefix="form" uri="http://www.springframework.org/tags/form"%>
<%@taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core"%>
<%@taglib prefix="spring" uri="http://www.springframework.org/tags"%>

<!DOCTYPE html>

<html>

<jsp:include page="header.jsp" />

	<body>


		<h1>Components</h1>
		<form:form action="addUser" method="post" modelAttribute="user">
			<table>
				<tr>
					<td>Name</td>
					<td>
						<form:input path="name" /> <br />
						<form:errors path="name" cssClass="error" />
					</td>
				</tr>
				<tr>
					<td>Email</td>
					<td>
						<form:input path="email" /> <br />
						<form:errors path="email" cssClass="error" />
					</td>
				</tr>
				<tr>
					<td colspan="2"><button type="submit">Submit</button></td>
				</tr>
			</table>
		</form:form>

		<hr> <!-- ------------------------------------------------------------------------------------------------ -->

		<div class="container">

			<c:if test="${not empty msg}">
				<div class="alert alert-${css} alert-dismissible" role="alert">
					<button type="button" class="close" data-dismiss="alert" aria-label="Close">
						<span aria-hidden="true">&times;</span>
					</button>
					<strong>${msg}</strong>
				</div>
			</c:if>

			<h1>All Users</h1>

			<table class="table table-striped">
				<thead>
				<tr>
					<th>Name</th>
					<th>Email</th>
				</tr>
				</thead>

				<c:forEach var="user" items="${users}">
					<tr>
						<td>${user.name}</td>
						<td>${user.email}</td>
						<td>
							<spring:url value="/users/${user.name}" var="userUrl" />
							<spring:url value="/users/${user.name}/delete" var="deleteUrl" />
							<spring:url value="/users/${user.name}/update" var="updateUrl" />

							<button class="btn btn-info" onclick="location.href='${userUrl}'">Query</button>
							<button class="btn btn-primary" onclick="location.href='${updateUrl}'">Update</button>
							<button class="btn btn-danger" onclick="this.disabled=true;location.href='${deleteUrl}'">Delete</button></td>
					</tr>
				</c:forEach>
			</table>

		</div>

		<hr> <!-- ------------------------------------------------------------------------------------------------ -->

		<jsp:include page="footer.jsp" />

	</body>
</html>
