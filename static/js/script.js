document.addEventListener('DOMContentLoaded', function () {
    const darkModeSwitch = document.getElementById('darkModeSwitch');
    const rootElement = document.documentElement; // Get the root element
  
    // Function to toggle dark mode
    const toggleDarkMode = () => {
      const isDarkModeActive = darkModeSwitch.checked;
  
      // Toggle the dark mode class on the root element (HTML)
      rootElement.classList.toggle('dark-mode', isDarkModeActive);
    };
  
    // Add an event listener for the dark mode switch
    darkModeSwitch.addEventListener('change', toggleDarkMode);
  
    
    
    
  });
  