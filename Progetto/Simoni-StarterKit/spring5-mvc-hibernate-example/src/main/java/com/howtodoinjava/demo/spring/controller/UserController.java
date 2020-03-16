package com.howtodoinjava.demo.spring.controller;

import java.util.Locale;

import javax.validation.Valid;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;

import com.howtodoinjava.demo.spring.model.User;
import com.howtodoinjava.demo.spring.service.UserService;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

//@Controller
public class UserController {

	@Autowired
	private UserService userService;

	@GetMapping("/")
	public String userForm(Locale locale, Model model) {
		model.addAttribute("users", userService.list());
		return "editUsers";
	}
	
	@ModelAttribute("user")
    public User formBackingObject() {
        return new User();
    }

	@PostMapping("/addUser")
	public String saveUser(@ModelAttribute("user") @Valid User user, BindingResult result, Model model) {

		if (result.hasErrors()) {
			model.addAttribute("users", userService.list());
			return "editUsers";
		}

		userService.save(user);
		return "redirect:/";
	}

	// delete user
	@RequestMapping(value = "/users/{name}/delete", method = RequestMethod.GET)
	public String deleteUser(@PathVariable("name") String name, final RedirectAttributes redirectAttributes) {

		System.out.println("deleteUser() : {}" + name);

		userService.delete(name);

		redirectAttributes.addFlashAttribute("css", "success");
		redirectAttributes.addFlashAttribute("msg", "User is deleted!");

		return "redirect:/";

	}
}
