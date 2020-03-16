package com.howtodoinjava.demo.spring.controller;

import com.howtodoinjava.demo.spring.model.Component;
import com.howtodoinjava.demo.spring.service.ComponentService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import javax.servlet.http.HttpServletRequest;
import javax.validation.Valid;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;


@Controller
public class ComponentController {

    @Autowired
    private ComponentService componentService;

    @GetMapping("/")
    public String componentForm(Locale locale, Model model) {
        model.addAttribute("components", componentService.list());
        //componentService.metodoInit();
        return "home";
    }

    @ModelAttribute("component")
    public Component formBackingObject() {
        return new Component();
    }

    @PostMapping("/addComponent")
    public String saveComponent(@ModelAttribute("component") @Valid Component component, BindingResult result, Model model, HttpServletRequest request) {

        if (result.hasErrors()) {
            model.addAttribute("components", componentService.list());
            return "home";
        }

        int num = 1;
        if (request.getParameter("num") != null)
              num = Integer.parseInt(request.getParameter("num"));

        for( int i=0; i< num; i++) {
            componentService.save(component);
            }

        return "redirect:/";
    }

    @RequestMapping(value="/execute", method = RequestMethod.POST)
    public void execute(HttpServletRequest request) throws IOException{

        System.setErr(new PrintStream("stderr.txt"));
        //System.out.println(request.getParameter("uc1") + " " + request.getParameter("uc2") + " " + request.getParameter("opt1"));
        Process process = null;

        List<Component> components = componentService.list();
        int size = components.size();


        FileWriter fileWriter = new FileWriter("config.conf");
        PrintWriter printWriter = new PrintWriter(fileWriter);
        System.out.println("CIAOOO");
        for(int i=0; i<size; i++){
            System.out.println("AAAAAAAAA");
            String components_list = components.get(i).getList().toString();
            //System.out.println("mI CHIAMO PAOLO E FACCIO IL CASSIERE AL SUPERMERCATO");
            components_list = components_list.replace(" ", ""); //per rimuovere gli spazi nella lista
            printWriter.print("pod:"+ i + ":" + i%100 + ":" + components_list + "\n");
            System.out.println("BBBBBBBBBBBBB");
        }
        printWriter.close();
        System.out.println("CCCCCCCCCC");

        try {
                process = Runtime.getRuntime().exec("python sample.py ");

        } catch (Exception e) {
            System.out.println("Exception Raised" + e.toString());
        }
        InputStream stdout = process.getInputStream();
        BufferedReader reader = new BufferedReader(new InputStreamReader(stdout, StandardCharsets.UTF_8));
        String line;
        try {
            while ((line = reader.readLine()) != null) {
                System.out.println("stdout: " + line);
            }
        } catch (IOException e) {
            System.out.println("Exception in reading output" + e.toString());
        }
    }

    // delete component
    @RequestMapping(value = "/components/{id}/delete", method = RequestMethod.GET)
    public String deleteComponent(@PathVariable("id") Long id, final RedirectAttributes redirectAttributes) {

        System.out.println("deleteComponent() : {}" + id);

        componentService.delete(id);

        redirectAttributes.addFlashAttribute("css", "success");
        redirectAttributes.addFlashAttribute("msg", "Component is deleted!");

        return "redirect:/";

    }

}



