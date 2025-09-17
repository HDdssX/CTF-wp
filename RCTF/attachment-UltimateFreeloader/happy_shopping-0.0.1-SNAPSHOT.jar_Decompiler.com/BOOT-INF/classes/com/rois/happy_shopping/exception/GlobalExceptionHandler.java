package com.rois.happy_shopping.exception;

import com.rois.happy_shopping.common.Result;
import java.util.HashMap;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.validation.BindException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {
   @ExceptionHandler({MethodArgumentNotValidException.class})
   @ResponseStatus(HttpStatus.BAD_REQUEST)
   public Result<?> handleValidationExceptions(MethodArgumentNotValidException ex) {
      Map<String, String> errors = new HashMap();
      ex.getBindingResult().getAllErrors().forEach((error) -> {
         String fieldName = ((FieldError)error).getField();
         String errorMessage = error.getDefaultMessage();
         errors.put(fieldName, errorMessage);
      });
      return Result.error(400, "参数验证失败：" + errors.toString());
   }

   @ExceptionHandler({BindException.class})
   @ResponseStatus(HttpStatus.BAD_REQUEST)
   public Result<?> handleBindException(BindException ex) {
      StringBuilder sb = new StringBuilder();
      ex.getFieldErrors().forEach((error) -> {
         sb.append(error.getField()).append(": ").append(error.getDefaultMessage()).append("; ");
      });
      return Result.error(400, "参数绑定失败：" + sb.toString());
   }

   @ExceptionHandler({RuntimeException.class})
   @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
   public Result<?> handleRuntimeException(RuntimeException ex) {
      return Result.error(500, "系统异常：" + ex.getMessage());
   }

   @ExceptionHandler({Exception.class})
   @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
   public Result<?> handleException(Exception ex) {
      return Result.error(500, "未知异常：" + ex.getMessage());
   }
}
