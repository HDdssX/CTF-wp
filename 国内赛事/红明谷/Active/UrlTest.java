public class UrlTest {
  public static void main(String[] args) throws Exception {
    for (String s : new String[]{"http://116.62.211.91/xxe_leak/flag{test}","http://116.62.211.91/xxe_leak?d=flag{test}","http://116.62.211.91/xxe_leak/flag_test","http://116.62.211.91/xxe_leak?d=flag_test"}) {
      try {
        java.net.URL u = new java.net.URL(s);
        System.out.println("OK " + u);
      } catch (Exception e) {
        System.out.println("ERR " + s + " :: " + e);
      }
    }
  }
}
